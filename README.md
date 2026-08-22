# PixelCraft
将任意图片转换为像素画的桌面工具，支持拖拽、实时预览和复古色盘。A GUI tool to convert any image into pixel art with retro palettes and real-time preview.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## ✨ 功能亮点
- 🖱️ **拖拽或点击加载**：支持直接拖拽图片到窗口，或通过按钮选择
- 📁 **批量处理 + 翻页浏览**：选择文件夹，逐张查看并调整参数
- 🎛️ **实时自动转换**：调节滑块时自动生成像素画，无需手动点击
- 🎨 **复古色盘预设**：内置 GameBoy、NES、CGA 等经典配色
- ✏️ **像素画编辑器**：点击修改任意像素块，支持撤销/重做
- 🔍 **图片缩放**：滚轮缩放 + 按钮控制 + 双击重置，原图和像素画同步
- 📐 **预设尺寸**：一键切换 16×16 / 32×32 / 64×64
- 💾 **保存导出**：支持 PNG / JPG / BMP 格式
- 🖥️ **自适应窗口**：窗口自由缩放，图片始终居中显示
- 🐧 **Linux 字体检测**：自动检测中文字体，缺失时弹窗提示
- 🔄 **滑块滚轮支持**：滚轮直接调节参数，操作更快捷

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
```bash
python pixel_craft.py
```

-注：如果 tkinterdnd2 安装失败，程序会自动降级运行（仅失去拖拽功能，其他正常）。

## 打包为可执行文件
-Windows
```bash
pyinstaller --onefile --windowed --collect-all tkinterdnd2 --name PixelCraft pixel_craft.py
```
-Linux / macOS
```bash
pyinstaller --onefile --name PixelCraft pixel_craft.py
```
打包后的文件在 dist 文件夹中，双击即可运行。

## 使用 Makefile（推荐）
```bash
make install    # 安装依赖
make build      # 打包
make run        # 直接运行
make clean      # 清理临时文件
```

如果你是Linux用户并且打开界面中文显示为方块，请安装中文字体：
```bash
sudo apt install fonts-noto-cjk fonts-wqy-microhei
```
