# PixelCraft
将任意图片转换为像素画的桌面工具，支持拖拽、实时预览和复古色盘。A GUI tool to convert any image into pixel art with retro palettes and real-time preview.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## ✨ 功能亮点
- 🖱️ **拖拽或点击加载**：支持直接拖拽图片到窗口，也可以通过「选择图片」按钮浏览文件
- 📁 **批量处理 + 翻页浏览**：选择文件夹，快速加载图片列表，逐张查看并调整参数
- 🎛️ **实时自动转换**：调节滑块时自动生成像素画，无需手动点击
- 🎨 **复古色盘预设**：内置 GameBoy、NES、CGA、Commodore 64、ZX Spectrum、Atari 2600、PICO-8 等经典配色
- ✏️ **像素画编辑器**：支持画笔/橡皮/框选/填充/吸管，可复制/粘贴/移动像素区域，支持撤销/重做
- 🔍 **对比视图**：原图与像素画左右并排，拖拽分割线对比细节
- 🔍 **图片缩放**：滚轮缩放 + 按钮控制 + 双击重置，原图和像素画同步
- 📜 **滚动条同步**：原图和像素画同步滚动，放大查看细节
- 🖱️ **拖拽平移视图**：长按图片拖拽即可平移画布
- 📐 **预设尺寸**：一键切换 16×16 / 32×32 / 64×64 / 128×128
- 💾 **保存导出**：支持 **PNG / JPG / BMP / SVG** 格式
- 🖥️ **自适应窗口**：窗口自由缩放，原图和像素画始终保持等宽
- 🔄 **滑块滚轮支持**：滚轮直接调节参数，操作更快捷
- 📂 **菜单栏**：完整的文件/编辑/帮助菜单，操作更专业

## 🚀 快速开始
### 1. 克隆仓库
```bash
git clone https://github.com/Grass114/PixelCraft.git
cd PixelCraft
```
### 2.安装依赖
```bash
pip install -r requirements.txt
```
### 3.运行程序
- Windows
```bash
python Windows-src/pixel_craft.py
```
- Linux / MacOS
```bash
python Linux-src/pixel_craft.py
```

-注：如果 tkinterdnd2 安装失败，程序会自动降级运行（仅失去拖拽功能，其他正常）。

## 打包为可执行文件
- Windows
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --collect-all tkinterdnd2 --name PixelCraft Windows-src/pixel_craft.py
```
- Linux / macOS
```bash
pip install pyinstaller
pyinstaller --onefile --name PixelCraft Linux-src/pixel_craft.py
```
打包后的文件在 dist 文件夹中，双击即可运行。

## 🛠️ Linux 开发者编译指南 (从源码打包)

如果你想自己修改 Linux 版源码并重新打包，本项目为你准备了极其完善的自动化脚本。

### 方式一：使用 Docker 打包（强烈推荐，兼容性最好）
此方法会将打包环境隔离在 Ubuntu 20.04 容器中，确保打出来的 AppImage 在老版本 Linux 上也能运行。

1. **安装 Docker**（如果你还没有安装）：
   `sudo bash install-docker.sh`
   *(注：脚本已内置国内加速源。安装后需注销重新登录或执行 `newgrp docker`)*
2. **一键打包**：
   `sudo ./build-appimage.sh --docker`

### 方式二：本地直接打包
如果本地环境满足 `python3`, `python3-tk`, `binutils`，直接执行：
`chmod +x build-appimage.sh`
`./build-appimage.sh --local`

打包完成后，根目录下会生成 `PixelCraft-x86_64.AppImage`。

## 🛠️ Linux 常见问题与解决方案 (Troubleshooting & FAQ)

由于 Linux 发行版生态繁杂，如果你在运行或打包时遇到问题，请先查阅以下解决方案：

### 一、 普通用户运行 AppImage 遇到的问题

#### 1. 双击 AppImage 没有任何反应，或者提示 "Permission denied"
**原因**：下载的文件默认没有执行权限。
**解决方案**：
打开终端，进入文件所在目录，执行 `chmod +x PixelCraft-x86_64.AppImage`，或者右键文件 -> 属性 -> 权限 -> 勾选“允许作为程序执行”。

#### 2. 运行报错 `dlopen(): error loading libfuse.so.2`
**原因**：你的系统较新（如 Ubuntu 24.04 / Linux Mint 22），默认只安装了 FUSE 3，而 AppImage 仍然依赖 FUSE 2。
**解决方案**：
- Ubuntu / Debian / Linux Mint: `sudo apt install libfuse2`
- Fedora: `sudo dnf install fuse-libs`

#### 3. 启动时突然闪退，终端输出 `X Error of failed request: BadLength (RenderAddGlyphs)`
**原因**：这是 Linux 下 Tkinter 渲染彩色 Emoji 字体时的已知底层 Bug，超出了 X11 协议的请求限制。
**解决方案**（无需重新打包，安装备用字体即可）：
`sudo apt update`
`sudo apt install unifont`

### 二、 开发者编译打包遇到的问题

#### 1. 运行 `build-appimage.sh` 提示找不到 Docker？
**解决方案**：
1. 请确保你已经运行了本仓库提供的 `install-docker.sh` 脚本。
2. 安装完成后，你需要**注销当前系统并重新登录**（或者重启），以便让当前用户加入 `docker` 用户组生效。
3. 如果你不想重新登录，可以在打包时临时使用 `sudo`：`sudo ./build-appimage.sh --docker`

#### 2. Docker 打包时报错 `Could not resolve host` 或下载软件包极慢
**解决方案**：
本项目的 `install-docker.sh` 和 `build-appimage.sh` 已经内置了阿里云镜像加速。如果依然失败，请检查宿主机的 DNS 配置。可以尝试在宿主机执行以下命令强制写入公共 DNS：
`echo "nameserver 223.5.5.5" | sudo tee /etc/resolv.conf`

#### 3. 打包报错 `Python shared library ('libpython3.8.so.1.0') was not found`
**解决方案**：
本项目最新的打包脚本已经在 `docker run` 的 `apt-get install` 列表中补全了 `libpython3.8` 和 `python3-dev`。请确保你使用的是最新版本的 `build-appimage.sh`。

#### 4. AppImage 打包成功，但拖拽功能无法使用
**解决方案**：
本项目最新的打包脚本中，已经为 `pyinstaller` 命令添加了 `--collect-all tkinterdnd2` 参数。请确保你使用的源码是最新版。

#### 5. `appimagetool` 报错 `More than one architectures were found...`
**解决方案**：
打包脚本已经通过强制传入环境变量 `ARCH="x86_64"` 修复了此问题。如果你自己手动打包遇到了，请在执行命令前加上 `ARCH=x86_64`。

## 使用 Makefile（推荐）
```bash
make install    # 安装依赖
make build      # 打包
make run        # 直接运行
make clean      # 清理临时文件
```
本项目采用 MIT License 授权。
