# PixelCraft
将任意图片转换为像素画的桌面工具，支持拖拽、实时预览和复古色盘。A GUI tool to convert any image into pixel art with retro palettes and real-time preview.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

---
## ✨ 功能亮点
- 🖱️ **拖拽或点击加载**：支持直接拖拽图片到窗口，或通过按钮选择
- 🎛️ **实时自动转换**：调节滑块时自动生成像素画，无需手动点击
- 🎨 **复古色盘预设**：内置 GameBoy、NES、CGA 等经典配色
- 📐 **网格尺寸显示**：底部状态栏实时显示像素网格宽高
- 💾 **保存导出**：支持导出 PNG / JPG 格式
- 🖥️ **自适应窗口**：窗口自由缩放，图片始终居中显示

---
## 🚀 快速开始
### 1. 克隆仓库
git clone https://github.com/Grass114/PixelCraft.git

cd PixelCraft
### 2.安装依赖
pip install -r requirements.txt
### 3.运行程序
python pixel_craft.py

-注：如果 tkinterdnd2 安装失败，程序会自动降级运行（仅失去拖拽功能，其他正常）。
