#!/usr/bin/env bash
# ============================================================
# 一键安装并配置 Docker (高健壮性/自动修复依赖/国内网络加速版)
# 适用系统: Ubuntu / Linux Mint / Debian
# 用法: sudo bash install-docker.sh
# ============================================================

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

info() { echo -e "${BLUE}[信息]${NC} $*"; }
ok()   { echo -e "${GREEN}[成功]${NC} $*"; }
err()  { echo -e "${RED}[错误]${NC} $*" >&2; }

# 1. 检查是否使用了 root 或 sudo 运行
if [ "$EUID" -ne 0 ]; then
    err "请使用 sudo 运行此脚本！"
    echo "例如: sudo bash $0"
    exit 1
fi

# 2. 清理之前因脚本错误导致的残留和破坏的依赖
info "正在清理旧版本残留并修复系统依赖 (这可能需要一点时间)..."
apt-get remove -y docker docker-engine docker.io containerd runc podman-docker >/dev/null 2>&1 || true
rm -f /etc/apt/sources.list.d/docker.list /etc/apt/sources.list.d/docker-ce.list
dpkg --configure -a >/dev/null 2>&1 || true
apt-get install -f -y >/dev/null 2>&1 || true

# 3. 安装基础依赖
info "安装基础依赖 (curl, ca-certificates)..."
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg

# 4. 精准识别系统版本 (完美解决 Linux Mint 被误判为 Debian 的问题)
info "正在识别系统类型和版本..."
source /etc/os-release

if [[ "$ID" == "ubuntu" || "$ID_LIKE" == *"ubuntu"* ]]; then
    DISTRO="ubuntu"
    # 如果是 Linux Mint，使用其底层的 Ubuntu 代号 (如 noble, jammy)
    CODENAME=${UBUNTU_CODENAME:-$VERSION_CODENAME}
elif [[ "$ID" == "debian" ]]; then
    DISTRO="debian"
    CODENAME=$VERSION_CODENAME
else
    err "未支持的系统！当前系统 ID: $ID"
    exit 1
fi
info "识别结果: 发行版 $DISTRO, 代号 $CODENAME"

# 5. 添加阿里云 Docker GPG 密钥和软件源 (国内加速)
info "配置 Docker 阿里云镜像源..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL "https://mirrors.aliyun.com/docker-ce/linux/$DISTRO/gpg" | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/$DISTRO $CODENAME stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 6. 安装 Docker Engine
info "更新软件源并安装 Docker..."
apt-get update -qq
# 如果依赖有冲突，强制修复
apt-get install -y --fix-broken docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 7. 配置 Docker 镜像加速器
info "配置 Docker Hub 镜像加速 (daemon.json)..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com",
    "https://docker.nju.edu.cn"
  ]
}
EOF

# 8. 启动 Docker 并设置开机自启
info "启动 Docker 服务..."
systemctl daemon-reload
systemctl enable docker >/dev/null 2>&1
systemctl restart docker

# 9. 将当前用户加入 docker 组 (免 sudo)
if [ -n "$SUDO_USER" ]; then
    info "将用户 $SUDO_USER 加入 docker 组..."
    usermod -aG docker "$SUDO_USER"
    ok "已加入。注意：你需要运行 'newgrp docker' 或者注销重新登录才能生效。"
fi

# 10. 验证安装
info "验证 Docker 是否安装成功..."
if docker info >/dev/null 2>&1; then
    ok "🎉 Docker 安装成功，并且镜像加速已生效！"
    echo "----------------------------------------"
    echo "当前 Docker 版本:"
    docker --version
    echo "----------------------------------------"
else
    err "Docker 似乎没有正常运行，请检查 'systemctl status docker' 查看原因。"
    exit 1
fi