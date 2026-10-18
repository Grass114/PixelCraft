#!/usr/bin/env bash
# ============================================================
# PixelCraft 一键打包 AppImage (Docker/本地双模式，终极完美版)
# ============================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()  { echo -e "${BLUE}[信息]${NC} $*"; }
ok()    { echo -e "${GREEN}[成功]${NC} $*"; }
warn()  { echo -e "${YELLOW}[警告]${NC} $*"; }
error() { echo -e "${RED}[错误]${NC} $*" >&2; }

show_help() {
    cat << 'EOF'
PixelCraft AppImage 打包脚本

用法:
  ./build-appimage.sh              交互式询问打包模式
  ./build-appimage.sh --auto       自动模式（有 Docker 用 Docker，否则本地）
  ./build-appimage.sh --docker     强制 Docker 打包（ubuntu:20.04，兼容旧系统）
  ./build-appimage.sh --local      强制本地打包
  ./build-appimage.sh --help       显示此帮助
EOF
}

# ---------- 依赖安装函数 ----------
install_dependencies() {
    info "正在下载并安装依赖 (Pillow / PyInstaller / Tkinterdnd2)..."
    echo "----------------------------------------"
    
    # 使用清华源加速，并确保安装了 tkinterdnd2
    if ! pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip pillow pyinstaller tkinterdnd2; then
        echo "----------------------------------------"
        error "依赖安装失败！"
        warn "可能是网络问题，请检查网络连接。"
        exit 1
    fi
    
    echo "----------------------------------------"
    ok "依赖安装完成。"
}

# ---------- 检测 Docker ----------
DOCKER_OK=0
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    DOCKER_OK=1
fi

# ---------- 参数解析 ----------
BUILD_MODE=""
for arg in "$@"; do
    case "$arg" in
        --auto)   BUILD_MODE="auto" ;;
        --docker) BUILD_MODE="docker" ;;
        --local)  BUILD_MODE="local" ;;
        --help|-h) show_help; exit 0 ;;
        *) error "未知参数: $arg"; show_help; exit 1 ;;
    esac
done

# ---------- 交互询问 ----------
if [[ -z "$BUILD_MODE" ]]; then
    if [[ -t 0 && -t 1 ]]; then
        echo
        echo "=============================================="
        echo "         PixelCraft AppImage 打包"
        echo "=============================================="
        if [[ $DOCKER_OK -eq 1 ]]; then
            echo "  Docker 状态: 已检测到（推荐使用，兼容旧系统）"
        else
            echo "  Docker 状态: 未检测到（将只能本地打包）"
        fi
        echo "----------------------------------------------"
        echo "  请选择打包模式："
        echo
        echo "    1) Docker 打包（ubuntu:20.04，兼容旧系统）  推荐"
        echo "    2) 本地打包（兼容性取决于当前系统的 glibc）"
        echo "    3) 自动选择（有 Docker 就用 Docker，否则本地）"
        echo "    4) 退出"
        echo
        while true; do
            read -r -p "请输入选项 [1-4，默认 3]: " choice
            choice="${choice:-3}"
            case "$choice" in
                1)
                    if [[ $DOCKER_OK -ne 1 ]]; then
                        warn "未检测到可用的 Docker，请先安装并启动 Docker。"
                        continue
                    fi
                    BUILD_MODE="docker"; break ;;
                2) BUILD_MODE="local"; break ;;
                3) BUILD_MODE="auto"; break ;;
                4) info "已取消"; exit 0 ;;
                *) warn "无效选项，请输入 1-4";;
            esac
        done
        echo
    else
        BUILD_MODE="auto"
    fi
fi

# ---------- 路径与变量 ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -z "${ENTRY:-}" ]]; then
    if [[ -f "src/pixel_craft.py" ]]; then
        ENTRY="src/pixel_craft.py"
    elif [[ -f "pixel_craft.py" ]]; then
        ENTRY="pixel_craft.py"
    else
        error "找不到 pixel_craft.py（既不在 src/ 也不在根目录）"
        exit 1
    fi
fi
info "入口文件: $ENTRY"

APP_NAME="${APP_NAME:-PixelCraft}"
VENV_DIR="${VENV_DIR:-.venv-build}"
APP_DIR="AppDir"
BUILD_DIR="dist/${APP_NAME}"
TOOL_CACHE=".appimagetool"

ARCH="$(uname -m)"
case "$ARCH" in
    x86_64) APPIMAGE_ARCH="x86_64" ;;
    aarch64|arm64) APPIMAGE_ARCH="aarch64" ;;
    *) error "不支持的架构: $ARCH"; exit 1 ;;
esac
OUTPUT_FILE="${APP_NAME}-${APPIMAGE_ARCH}.AppImage"

# ============================================================
# Docker 判断
# ============================================================
USE_DOCKER=0
if [[ "${PIXELCRAFT_IN_DOCKER:-0}" != "1" ]]; then
    case "$BUILD_MODE" in
        docker)
            if [[ $DOCKER_OK -ne 1 ]]; then
                error "选择了 Docker 打包，但未检测到可用的 Docker"
                exit 1
            fi
            USE_DOCKER=1 ;;
        local) USE_DOCKER=0 ;;
        auto)  [[ $DOCKER_OK -eq 1 ]] && USE_DOCKER=1 || USE_DOCKER=0 ;;
    esac
fi

# ============================================================
# Docker 分支
# ============================================================
if [[ $USE_DOCKER -eq 1 ]]; then
    info "使用 Docker 打包（ubuntu:20.04，glibc 2.31）"
    echo

    if command -v cygpath >/dev/null 2>&1; then
        MOUNT_PATH="$(cygpath -w "$PWD")"
    else
        MOUNT_PATH="$PWD"
    fi

    docker run --rm \
        -v "${MOUNT_PATH}:/app" -w /app \
        -e PIXELCRAFT_IN_DOCKER=1 \
        -e APPIMAGE_EXTRACT_AND_RUN=1 \
        -e VENV_DIR=".venv-build-docker" \
        -e ENTRY="$ENTRY" \
        -e HOST_UID="$(id -u)" \
        -e HOST_GID="$(id -g)" \
        ubuntu:20.04 bash -c '
            set -e
            export DEBIAN_FRONTEND=noninteractive
            # 换阿里云源加速
            sed -i "s@http://archive.ubuntu.com/ubuntu/@http://mirrors.aliyun.com/ubuntu/@g" /etc/apt/sources.list
            sed -i "s@http://security.ubuntu.com/ubuntu/@http://mirrors.aliyun.com/ubuntu/@g" /etc/apt/sources.list
            apt-get update -qq >/dev/null
            # 安装所有必需的依赖，包括 binutils, libpython3.8, python3-dev
            apt-get install -y -qq python3 python3-tk python3-venv wget curl file binutils libpython3.8 python3-dev >/dev/null
            chmod +x build-appimage.sh
            ./build-appimage.sh --local

            chown -R "$HOST_UID:$HOST_GID" AppDir dist build .venv-build-docker 2>/dev/null || true
            find . -maxdepth 1 -name "*.AppImage" -exec chown "$HOST_UID:$HOST_GID" {} + 2>/dev/null || true
            find . -maxdepth 1 -name "*.spec" -exec chown "$HOST_UID:$HOST_GID" {} + 2>/dev/null || true
        '

    echo
    ok "Docker 打包完成: $SCRIPT_DIR/$OUTPUT_FILE"
    exit 0
fi

# ============================================================
# 本地打包分支
# ============================================================
info "本地打包模式（$(uname -s) $(uname -r)，$ARCH）"
if [[ "${PIXELCRAFT_IN_DOCKER:-0}" != "1" ]]; then
    warn "本地打包的 AppImage 兼容性取决于当前系统的 glibc"
fi
echo

info "检查入口文件: $ENTRY"
[[ -f "$ENTRY" ]] || { error "找不到 $ENTRY"; exit 1; }

command -v python3 >/dev/null 2>&1 || { error "未找到 python3"; exit 1; }

if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    error "Python 缺少 tkinter 模块，请先安装："
    echo "  Debian/Ubuntu: sudo apt install python3-tk"
    echo "  Fedora:        sudo dnf install python3-tkinter"
    exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
    info "创建虚拟环境: $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ---- 安装依赖 ----
install_dependencies

info "清理旧的构建产物"
rm -rf build "$BUILD_DIR" "$APP_DIR" "$OUTPUT_FILE" "${APP_NAME}.spec"

info "PyInstaller 打包（目录模式）"
# 关键修复：增加 --collect-all tkinterdnd2，解决拖拽功能不可用问题
pyinstaller --windowed --name "$APP_NAME" \
    --hidden-import="PIL._tkinter_finder" \
    --hidden-import="PIL._imagingtk" \
    --collect-all tkinterdnd2 \
    --noconfirm "$ENTRY"

[[ -x "$BUILD_DIR/$APP_NAME" ]] || { error "PyInstaller 打包失败"; exit 1; }
ok "PyInstaller 完成"

info "组装 AppDir"
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/share/applications"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"

cp -r "$BUILD_DIR/." "$APP_DIR/usr/bin/"

# ==========================================
# 【智能识别图标】
# ==========================================
info "准备图标..."
if [[ -f "icon.png" ]]; then
    info "✅ 检测到自定义图标 icon.png，正在使用..."
    cp "icon.png" "$APP_DIR/usr/share/icons/hicolor/256x256/apps/pixelcraft.png"
    cp "icon.png" "$APP_DIR/pixelcraft.png"
else
    info "⚠️ 未检测到 icon.png，自动生成默认图标..."
    python3 -c "
from PIL import Image, ImageDraw
img = Image.new('RGBA', (256, 256), (26, 26, 46, 255))
draw = ImageDraw.Draw(img)
draw.rectangle([64, 64, 192, 192], fill=(240, 136, 62, 255))
draw.rectangle([96, 96, 160, 160], fill=(255, 255, 255, 255))
img.save('$APP_DIR/usr/share/icons/hicolor/256x256/apps/pixelcraft.png')
img.save('$APP_DIR/pixelcraft.png')
"
fi

cat > "$APP_DIR/pixelcraft.desktop" << DESKTOP_EOF
[Desktop Entry]
Name=${APP_NAME}
Comment=将图片转换为像素画
Exec=${APP_NAME}
Icon=pixelcraft
Type=Application
Categories=Graphics;
Terminal=false
StartupNotify=true
DESKTOP_EOF
cp "$APP_DIR/pixelcraft.desktop" "$APP_DIR/usr/share/applications/"

cat > "$APP_DIR/AppRun" << APP_RUN_EOF
#!/bin/bash
SELF=\$(readlink -f "\$0")
HERE=\${SELF%/*}
export PATH="\$HERE/usr/bin:\$PATH"
exec "\$HERE/usr/bin/${APP_NAME}" "\$@"
APP_RUN_EOF
chmod +x "$APP_DIR/AppRun"

# ---------- 下载 appimagetool ----------
if [[ ! -x "$TOOL_CACHE" ]]; then
    info "下载 appimagetool ($APPIMAGE_ARCH)"
    URL="https://ghproxy.net/https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${APPIMAGE_ARCH}.AppImage"
    
    if command -v wget >/dev/null 2>&1; then
        wget --show-progress -O "$TOOL_CACHE" "$URL" || wget -q -O "$TOOL_CACHE" "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${APPIMAGE_ARCH}.AppImage"
    elif command -v curl >/dev/null 2>&1; then
        curl -L -# -o "$TOOL_CACHE" "$URL" || curl -L -# -o "$TOOL_CACHE" "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${APPIMAGE_ARCH}.AppImage"
    else
        error "需要 wget 或 curl 来下载 appimagetool"
        exit 1
    fi
    chmod +x "$TOOL_CACHE"
fi

# ==========================================
# 【预下载 Runtime 文件】
# ==========================================
RUNTIME_FILE=".runtime-${APPIMAGE_ARCH}"

if [[ ! -s "$RUNTIME_FILE" ]]; then
    info "检测到缺少运行时，正在下载 type2-runtime ($APPIMAGE_ARCH)..."
    RUNTIME_URL="https://ghproxy.net/https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-${APPIMAGE_ARCH}"
    
    if command -v wget >/dev/null 2>&1; then
        wget -q --show-progress -O "$RUNTIME_FILE" "$RUNTIME_URL" || {
            warn "代理源下载失败，尝试官方源..."
            wget -q --show-progress -O "$RUNTIME_FILE" "https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-${APPIMAGE_ARCH}"
        }
    elif command -v curl >/dev/null 2>&1; then
        curl -L -# -o "$RUNTIME_FILE" "$RUNTIME_URL" || {
            warn "代理源下载失败，尝试官方源..."
            curl -L -# -o "$RUNTIME_FILE" "https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-${APPIMAGE_ARCH}"
        }
    else
        error "需要 wget 或 curl 来下载运行时文件"
        exit 1
    fi
    
    if [[ ! -s "$RUNTIME_FILE" ]]; then
        error "运行时文件下载失败，请检查网络或手动下载至 $RUNTIME_FILE"
        rm -f "$RUNTIME_FILE"
        exit 1
    fi
    chmod +x "$RUNTIME_FILE"
fi

info "打包 AppImage"
# 关键修复：在执行 appimagetool 时强制传入 ARCH 环境变量，防止架构识别错误
if [[ "${APPIMAGE_EXTRACT_AND_RUN:-0}" == "1" ]]; then
    ARCH="$APPIMAGE_ARCH" "./$TOOL_CACHE" --appimage-extract-and-run --runtime-file "$RUNTIME_FILE" "$APP_DIR" "$OUTPUT_FILE"
else
    if ! ARCH="$APPIMAGE_ARCH" "./$TOOL_CACHE" --runtime-file "$RUNTIME_FILE" "$APP_DIR" "$OUTPUT_FILE" 2>/tmp/appimagetool.err; then
        if grep -qi "fuse" /tmp/appimagetool.err; then
            warn "检测到 FUSE 问题，改用解压模式重试"
            ARCH="$APPIMAGE_ARCH" "./$TOOL_CACHE" --appimage-extract-and-run --runtime-file "$RUNTIME_FILE" "$APP_DIR" "$OUTPUT_FILE"
        else
            cat /tmp/appimagetool.err
            error "appimagetool 打包失败"
            exit 1
        fi
    fi
fi

chmod +x "$OUTPUT_FILE"

echo
ok "打包完成: $SCRIPT_DIR/$OUTPUT_FILE"