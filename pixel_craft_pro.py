import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageDraw, ImageFont, ImageTk
import os
import threading
import time
from collections import Counter

# 尝试导入拖拽支持
try:
    from tkinterdnd2 import TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("提示：未安装 tkinterdnd2，拖拽功能不可用。安装：pip install tkinterdnd2")


# ---------- 调色板 ----------
PALETTES = {
    "自动": None,
    "GameBoy (4色)": [
        (15, 56, 15), (48, 98, 48), (139, 172, 15), (155, 188, 15)
    ],
    "NES (20色)": [
        (0, 0, 0), (255, 255, 255), (252, 0, 0), (0, 252, 0),
        (0, 0, 252), (252, 252, 0), (252, 0, 252), (0, 252, 252),
        (252, 128, 0), (0, 128, 0), (0, 0, 128), (128, 0, 128),
        (128, 128, 0), (0, 128, 128), (128, 128, 128), (192, 192, 192),
        (252, 128, 128), (128, 252, 128), (128, 128, 252), (252, 252, 128)
    ],
    "CGA 4色": [
        (0, 0, 0), (255, 255, 255), (0, 255, 255), (255, 0, 255)
    ],
    "CGA 16色": [
        (0,0,0), (0,0,170), (0,170,0), (0,170,170),
        (170,0,0), (170,0,170), (170,85,0), (170,170,170),
        (85,85,85), (85,85,255), (85,255,85), (85,255,255),
        (255,85,85), (255,85,255), (255,255,85), (255,255,255)
    ],
    "从图片提取": None,  # 特殊标记
}


class PixelCraftPro:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 PixelCraft Pro")
        self.root.geometry("800x620")
        self.root.minsize(700, 550)

        # 状态变量
        self.original_image = None      # PIL Image (RGBA 或 RGB)
        self.result_image = None        # PIL Image (最终结果)
        self.original_tk = None
        self.result_tk = None
        self.current_display_size = (0, 0)
        self.after_id = None
        self.extracted_palette = None   # 从图片提取的色板
        self.input_folder = None        # 批量处理用
        self.is_batch_mode = False

        # 设置拖拽
        if HAS_DND and isinstance(root, TkinterDnD.Tk):
            root.drop_target_register('DND_Files')
            root.dnd_bind('<<Drop>>', self.on_drop)

        self.setup_ui()
        self.update_status("拖拽图片或点击「选择图片」开始")

    # ---------- UI 布局 ----------
    def setup_ui(self):
        main = tk.Frame(self.root)
        main.pack(padx=10, pady=8, fill=tk.BOTH, expand=True)

        # ---- 顶部：文件选择 ----
        top = tk.Frame(main)
        top.pack(fill=tk.X, pady=(0, 8))

        tk.Button(top, text="📂 选择图片", command=self.load_single_image, width=12).pack(side=tk.LEFT, padx=(0,5))
        tk.Button(top, text="📁 批量处理", command=self.load_batch_folder, width=12).pack(side=tk.LEFT, padx=(0,5))
        self.file_label = tk.Label(top, text="未选择文件", anchor="w", relief="sunken")
        self.file_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # ---- 参数行 ----
        param = tk.Frame(main)
        param.pack(fill=tk.X, pady=(0, 8))

        # 块大小
        tk.Label(param, text="块:").pack(side=tk.LEFT)
        self.block_var = tk.IntVar(value=12)
        self.block_scale = tk.Scale(param, from_=2, to=30, orient=tk.HORIZONTAL,
                                    variable=self.block_var, length=120, showvalue=0)
        self.block_scale.pack(side=tk.LEFT, padx=(0,5))
        self.block_label = tk.Label(param, text="12", width=3)
        self.block_label.pack(side=tk.LEFT, padx=(0,15))
        self.block_scale.config(command=lambda v: (self.block_label.config(text=v), self.schedule_convert()))

        # 颜色数
        tk.Label(param, text="颜色:").pack(side=tk.LEFT)
        self.color_var = tk.IntVar(value=16)
        self.color_scale = tk.Scale(param, from_=2, to=64, orient=tk.HORIZONTAL,
                                    variable=self.color_var, length=120, showvalue=0)
        self.color_scale.pack(side=tk.LEFT, padx=(0,5))
        self.color_label = tk.Label(param, text="16", width=3)
        self.color_label.pack(side=tk.LEFT, padx=(0,10))
        self.color_scale.config(command=lambda v: (self.color_label.config(text=v), self.schedule_convert()))

        # 色盘
        tk.Label(param, text="色盘:").pack(side=tk.LEFT)
        self.palette_var = tk.StringVar(value="自动")
        self.palette_combo = ttk.Combobox(param, textvariable=self.palette_var,
                                          values=list(PALETTES.keys()), state="readonly", width=16)
        self.palette_combo.pack(side=tk.LEFT, padx=(0,10))
        self.palette_combo.bind("<<ComboboxSelected>>", lambda e: self.schedule_convert())

        # 提取主色按钮
        tk.Button(param, text="🎨 提取主色", command=self.extract_main_colors, width=10).pack(side=tk.LEFT)

        # ---- 图片显示 ----
        display = tk.Frame(main)
        display.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        left = tk.LabelFrame(display, text="原图")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5))
        self.orig_canvas = tk.Canvas(left, bg="#f0f0f0", highlightthickness=0)
        self.orig_canvas.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        right = tk.LabelFrame(display, text="像素画")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5,0))
        self.res_canvas = tk.Canvas(right, bg="#f0f0f0", highlightthickness=0)
        self.res_canvas.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # ---- 底部 ----
        bottom = tk.Frame(main)
        bottom.pack(fill=tk.X, pady=(0, 4))

        self.save_btn = tk.Button(bottom, text="💾 保存像素画", command=self.save_image,
                                  state=tk.DISABLED, bg="#2196F3", fg="white")
        self.save_btn.pack(side=tk.LEFT, padx=(0,10))

        self.cross_stitch_btn = tk.Button(bottom, text="🧵 导出十字绣图纸", command=self.save_cross_stitch,
                                          state=tk.DISABLED, bg="#4CAF50", fg="white")
        self.cross_stitch_btn.pack(side=tk.LEFT, padx=(0,10))

        self.status = tk.Label(bottom, text="就绪", fg="blue", anchor="w")
        self.status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 绑定窗口缩放
        self.root.bind("<Configure>", self.on_resize)

    # ---------- 拖拽支持 ----------
    def on_drop(self, event):
        files = event.data.split()
        if files:
            path = files[0].strip('{}')
            if os.path.isfile(path):
                self.load_image_path(path)

    # ---------- 加载图片 ----------
    def load_single_image(self):
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"), ("所有文件", "*.*")]
        )
        if path:
            self.load_image_path(path)

    def load_image_path(self, path):
        try:
            # 保留透明通道
            self.original_image = Image.open(path).convert("RGBA")
            self.file_label.config(text=os.path.basename(path))
            self.result_image = None
            self.res_canvas.delete("all")
            self.save_btn.config(state=tk.DISABLED)
            self.cross_stitch_btn.config(state=tk.DISABLED)
            self.current_display_size = (0, 0)
            self.is_batch_mode = False
            self.after_idle_refresh()
            self.update_status(f"已加载：{os.path.basename(path)}，自动转换中...")
            self.schedule_convert(immediate=True)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片：{e}")

    # ---------- 批量处理 ----------
    def load_batch_folder(self):
        folder = filedialog.askdirectory(title="选择包含图片的文件夹")
        if not folder:
            return
        self.input_folder = folder
        self.is_batch_mode = True
        self.update_status(f"批量模式：{folder}")

        # 获取所有图片
        exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
        files = [f for f in os.listdir(folder) if f.lower().endswith(exts)]
        if not files:
            messagebox.showinfo("提示", "该文件夹中没有找到图片文件")
            self.is_batch_mode = False
            return

        self.file_label.config(text=f"批量处理：{len(files)} 张图片")
        self.update_status(f"开始批量处理 {len(files)} 张图片...")

        # 在新线程中执行，避免界面卡顿
        threading.Thread(target=self.batch_process, args=(folder, files), daemon=True).start()

    def batch_process(self, folder, files):
        block = self.block_var.get()
        colors = self.color_var.get()
        palette_name = self.palette_var.get()
        palette = PALETTES.get(palette_name)

        output_folder = os.path.join(folder, "pixel_output")
        os.makedirs(output_folder, exist_ok=True)

        total = len(files)
        for i, fname in enumerate(files):
            self.root.after(0, lambda msg=f"处理中：{i+1}/{total} - {fname}": self.update_status(msg))
            try:
                img = Image.open(os.path.join(folder, fname)).convert("RGBA")
                result = self.process_image(img, block, colors, palette)
                if result:
                    base = os.path.splitext(fname)[0]
                    result.save(os.path.join(output_folder, f"{base}_pixel.png"))
            except Exception as e:
                print(f"处理 {fname} 失败：{e}")

        self.root.after(0, lambda: self.update_status(f"✅ 批量处理完成！共 {total} 张，保存在 {output_folder}"))
        self.root.after(0, lambda: messagebox.showinfo("完成", f"批量处理完成！\n共处理 {total} 张图片\n保存在：{output_folder}"))

    # ---------- 核心处理 ----------
    def process_image(self, img, block, colors, palette):
        w, h = img.size
        # 分离透明通道
        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            rgb_img = Image.merge('RGB', (r, g, b))
            has_alpha = True
        else:
            rgb_img = img.convert('RGB')
            has_alpha = False

        bw = max(1, w // block)
        bh = max(1, h // block)

        # 缩小
        small = rgb_img.resize((bw, bh), Image.NEAREST)

        # 量化
        if palette:
            small = self.apply_palette(small, palette)
        else:
            if colors < 256:
                small = small.quantize(colors=colors, method=Image.MEDIANCUT)
                small = small.convert('RGB')

        # 放大
        result_rgb = small.resize((w, h), Image.NEAREST)

        # 重新合成透明通道
        if has_alpha:
            # 把 alpha 也做同样的缩放
            small_a = a.resize((bw, bh), Image.NEAREST)
            result_a = small_a.resize((w, h), Image.NEAREST)
            result = Image.merge('RGBA', (*result_rgb.split(), result_a))
        else:
            result = result_rgb

        return result

    def apply_palette(self, image, palette_colors):
        pixels = image.load()
        w, h = image.size
        for y in range(h):
            for x in range(w):
                r, g, b = pixels[x, y]
                best = (r, g, b)
                min_dist = float('inf')
                for pr, pg, pb in palette_colors:
                    dist = (r-pr)**2 + (g-pg)**2 + (b-pb)**2
                    if dist < min_dist:
                        min_dist = dist
                        best = (pr, pg, pb)
                pixels[x, y] = best
        return image

    # ---------- 提取主色 ----------
    def extract_main_colors(self):
        if self.original_image is None:
            messagebox.showwarning("提示", "请先加载一张图片")
            return

        img = self.original_image.convert('RGB')
        # 缩小图片以加速
        small = img.resize((100, 100), Image.Resampling.LANCZOS)
        pixels = list(small.getdata())

        # 颜色量化
        quantized = Image.new('RGB', (100, 100))
        quantized.putdata(pixels)
        quantized = quantized.quantize(colors=12, method=Image.MEDIANCUT)
        quantized = quantized.convert('RGB')

        # 统计颜色
        colors = list(quantized.getdata())
        counter = Counter(colors)
        # 按出现次数排序，取前8种
        main_colors = [color for color, _ in counter.most_common(8)]

        # 存储到自定义调色板
        self.extracted_palette = main_colors
        PALETTES["🎨 提取色板"] = main_colors

        # 更新下拉框
        palette_list = list(PALETTES.keys())
        self.palette_combo['values'] = palette_list
        self.palette_var.set("🎨 提取色板")

        self.update_status(f"✅ 提取了 {len(main_colors)} 种主色")
        self.schedule_convert(immediate=True)

    # ---------- 转换调度 ----------
    def schedule_convert(self, immediate=False):
        if self.original_image is None or self.is_batch_mode:
            return
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if immediate:
            self.do_convert()
        else:
            self.after_id = self.root.after(200, self.do_convert)

    def do_convert(self):
        if self.original_image is None or self.is_batch_mode:
            return
        block = self.block_var.get()
        colors = self.color_var.get()
        palette_name = self.palette_var.get()
        palette = PALETTES.get(palette_name)

        try:
            img = self.original_image.copy()
            result = self.process_image(img, block, colors, palette)
            self.result_image = result
            self.show_image(result, self.res_canvas)
            self.save_btn.config(state=tk.NORMAL)
            self.cross_stitch_btn.config(state=tk.NORMAL)

            # 计算网格尺寸
            w, h = img.size
            bw = max(1, w // block)
            bh = max(1, h // block)
            self.update_status(f"✅ 块 {block} | 颜色 {colors} | 网格 {bw}×{bh}")
        except Exception as e:
            messagebox.showerror("转换错误", str(e))

    # ---------- 显示图片 ----------
    def show_image(self, pil_img, canvas):
        if pil_img is None:
            return
        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        if cw < 10 or ch < 10:
            return
        w, h = pil_img.size
        scale = min(cw / w, ch / h, 1.0)
        new_w = int(w * scale)
        new_h = int(h * scale)
        if new_w < 1 or new_h < 1:
            return
        if scale < 1.0:
            resized = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            resized = pil_img.copy()
        tk_img = ImageTk.PhotoImage(resized)
        canvas.delete("all")
        x = (cw - new_w) // 2
        y = (ch - new_h) // 2
        canvas.create_image(x, y, anchor=tk.NW, image=tk_img)
        if canvas == self.orig_canvas:
            self.original_tk = tk_img
        else:
            self.result_tk = tk_img

    # ---------- 保存普通图片 ----------
    def save_image(self):
        if self.result_image is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG图片", "*.png"), ("JPEG图片", "*.jpg")]
        )
        if path:
            try:
                self.result_image.save(path)
                self.update_status(f"✅ 已保存：{os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("保存错误", str(e))

    # ---------- 导出十字绣图纸 ----------
    def save_cross_stitch(self):
        if self.result_image is None:
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG图片", "*.png")]
        )
        if not path:
            return

        try:
            # 获取当前结果图
            img = self.result_image.copy()
            if img.mode == 'RGBA':
                # 透明背景填充为白色
                bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
                img = Image.alpha_composite(bg, img)
            img = img.convert('RGB')

            w, h = img.size
            # 确定网格大小（根据图片尺寸自动计算）
            grid_size = max(4, min(20, 400 // max(w, h) * 4))

            # 放大图纸
            scale = 400 // max(w, h) * 2
            scale = max(scale, 8)
            new_w = w * scale
            new_h = h * scale

            # 创建大图
            result = Image.new('RGB', (new_w + 100, new_h + 80), (255, 255, 255))
            draw = ImageDraw.Draw(result)

            # 绘制放大的像素块
            pixels = img.load()
            for y in range(h):
                for x in range(w):
                    color = pixels[x, y]
                    x0 = x * scale
                    y0 = y * scale
                    draw.rectangle([x0, y0, x0 + scale - 1, y0 + scale - 1], fill=color)

            # 绘制网格线
            for x in range(new_w + 1):
                draw.line([(x, 0), (x, new_h)], fill=(200, 200, 200), width=1)
            for y in range(new_h + 1):
                draw.line([(0, y), (new_w, y)], fill=(200, 200, 200), width=1)

            # 绘制色号对照表
            # 提取颜色
            color_map = {}
            for y in range(h):
                for x in range(w):
                    c = pixels[x, y]
                    if c not in color_map:
                        color_map[c] = len(color_map) + 1

            # 在右侧显示色号
            y_pos = 20
            for color, idx in color_map.items():
                x0 = new_w + 20
                draw.rectangle([x0, y_pos, x0 + 30, y_pos + 30], fill=color, outline=(0,0,0))
                draw.text((x0 + 35, y_pos + 8), f"#{idx}", fill=(0,0,0))
                y_pos += 40
                if y_pos > new_h:
                    break

            result.save(path)
            self.update_status(f"✅ 十字绣图纸已保存：{os.path.basename(path)}")

        except Exception as e:
            messagebox.showerror("导出错误", str(e))

    # ---------- 窗口缩放 ----------
    def on_resize(self, event):
        if self.original_image is None:
            return
        w = self.orig_canvas.winfo_width()
        h = self.orig_canvas.winfo_height()
        if w > 10 and h > 10 and (w, h) != self.current_display_size:
            self.current_display_size = (w, h)
            self.show_image(self.original_image, self.orig_canvas)
            if self.result_image:
                self.show_image(self.result_image, self.res_canvas)

    def after_idle_refresh(self):
        self.root.after(50, lambda: self.on_resize(None))

    def update_status(self, msg):
        self.status.config(text=msg)


# ---------- 启动 ----------
if __name__ == "__main__":
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = PixelCraftPro(root)
    root.mainloop()