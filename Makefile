# ============================================================
# PixelCraft Makefile
# ============================================================

.PHONY: help build clean run install

help:
	@echo "PixelCraft Makefile 命令:"
	@echo "  make install    - 安装 Python 依赖"
	@echo "  make build      - 打包成可执行文件"
	@echo "  make clean      - 清理临时文件"
	@echo "  make run        - 直接运行源码"

install:
	pip install -r requirements.txt

build:
	@echo "开始打包 PixelCraft..."
	pyinstaller --onefile --windowed --collect-all tkinterdnd2 --name PixelCraft src/pixel_craft.py
	@echo "打包完成！EXE 位于 dist/PixelCraft.exe"

build-dnd:
	@echo "打包 PixelCraft (含拖拽支持)..."
	pyinstaller --onefile --windowed --collect-all tkinterdnd2 --name PixelCraft src/pixel_craft.py
	@echo "打包完成！EXE 位于 dist/PixelCraft.exe"

run:
	python src/pixel_craft.py

clean:
	@echo "清理临时文件..."
	rm -rf build/ dist/ *.spec __pycache__/ src/__pycache__/
	@echo "清理完成！"