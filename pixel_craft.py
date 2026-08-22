import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageDraw, ImageTk
import os
import json

# 尝试导入拖拽支持
try:
    from tkinterdnd2 import TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("提示：未安装 tkinterdnd2，拖拽功能不可用。安装：pip install tkinterdnd2")


# 预设尺寸
PRESETS = {
    "16×16": (16, 16),
    "32×32": (32, 32),
    "48×48": (48, 48),
    "64×64": (64, 64),
    "128×128": (128, 128),
}

# 调色板
PALETTES = {
    "自动": None,
    "GameBoy (4色)": [(15, 56, 15), (48, 98, 48), (139, 172, 15), (155, 188, 15)],
    "NES (20色)": [
        (0, 0, 0), (255, 255, 255), (252, 0, 0), (0, 252, 0),
        (0, 0, 252), (252, 252, 0), (252, 0, 252), (0, 252, 252),
        (252, 128, 0), (0, 128, 0), (0, 0, 128), (128, 0, 128),
        (128, 128, 0), (0, 128, 128), (128, 128, 128), (192, 192, 192),
        (252, 128, 128), (128, 252, 128), (128, 128, 252), (252, 252, 128)
    ],
    "CGA 4色": [(0, 0, 0), (255, 255, 255), (0, 255, 255), (255, 0, 255)],
    "CGA 16色": [
        (0,0,0), (0,0,170), (0,170,0), (0,170,170),
        (170,0,0), (170,0,170), (170,85,0), (170,170,170),
        (85,85,85), (85,85,255), (85,255,85), (85,255,255),
        (255,85,85), (255,85,255), (255,255,85), (255,255,255)
    ],
}


class PixelCraft:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 PixelCraft")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # 状态变量
        self.original_image = None
        self.result_image = None
        self.orig_tk = None
        self.res_tk = None
        self.current_display_size = (0, 0)
        self.after_id = None
        self.zoom_factor = 1.0

        # 批量翻页相关
        self.batch_images = []
        self.batch_index = 0
        self.is_batch_mode = False

        # 编辑模式
        self.edit_window = None
        self.grid_colors = []
        self.grid_w = 0
        self.grid_h = 0
        self.undo_stack = []
        self.redo_stack = []
        self.current_color = (255, 0, 0)
        self.edit_tool = "brush"

        # 拖拽支持
        if HAS_DND and isinstance(root, TkinterDnD.Tk):
            root.drop_target_register('DND_Files')
            root.dnd_bind('<<Drop>>', self.on_drop)

        self.setup_ui()
        self.update_status("拖拽图片或点击「选择图片」开始")

    # ========== UI 布局 ==========
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

        # ---- 翻页行（批量模式显示） ----
        nav_frame = tk.Frame(main)
        nav_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.prev_btn = tk.Button(nav_frame, text="◀ 上一张", command=self.prev_image, state=tk.DISABLED, width=10)
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.page_label = tk.Label(nav_frame, text="", fg="#888", font=("Arial", 11))
        self.page_label.pack(side=tk.LEFT)
        
        self.next_btn = tk.Button(nav_frame, text="下一张 ▶", command=self.next_image, state=tk.DISABLED, width=10)
        self.next_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        self.save_batch_btn = tk.Button(nav_frame, text="💾 保存当前", command=self.save_current_batch,
                                         state=tk.DISABLED, bg="#4CAF50", fg="white", width=10)
        self.save_batch_btn.pack(side=tk.RIGHT)

        # ---- 参数行 ----
        param = tk.Frame(main)
        param.pack(fill=tk.X, pady=(0, 8))

        tk.Label(param, text="预设:").pack(side=tk.LEFT)
        self.preset_var = tk.StringVar(value="自定义")
        self.preset_combo = ttk.Combobox(param, textvariable=self.preset_var,
                                         values=["自定义"] + list(PRESETS.keys()),
                                         state="readonly", width=8)
        self.preset_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.preset_combo.bind("<<ComboboxSelected>>", self.on_preset_selected)

        tk.Label(param, text="块:").pack(side=tk.LEFT)
        self.block_var = tk.IntVar(value=12)
        self.block_scale = tk.Scale(param, from_=2, to=40, orient=tk.HORIZONTAL,
                                    variable=self.block_var, length=100, showvalue=0)
        self.block_scale.pack(side=tk.LEFT, padx=(0, 5))
        self.block_label = tk.Label(param, text="12", width=3)
        self.block_label.pack(side=tk.LEFT, padx=(0, 10))
        self.block_scale.config(command=lambda v: (self.block_label.config(text=v), self.on_block_changed()))

        tk.Label(param, text="颜色:").pack(side=tk.LEFT)
        self.color_var = tk.IntVar(value=16)
        self.color_scale = tk.Scale(param, from_=2, to=64, orient=tk.HORIZONTAL,
                                    variable=self.color_var, length=100, showvalue=0)
        self.color_scale.pack(side=tk.LEFT, padx=(0, 5))
        self.color_label = tk.Label(param, text="16", width=3)
        self.color_label.pack(side=tk.LEFT, padx=(0, 10))
        self.color_scale.config(command=lambda v: (self.color_label.config(text=v), self.on_block_changed()))

        tk.Label(param, text="色盘:").pack(side=tk.LEFT)
        self.palette_var = tk.StringVar(value="自动")
        self.palette_combo = ttk.Combobox(param, textvariable=self.palette_var,
                                          values=list(PALETTES.keys()), state="readonly", width=14)
        self.palette_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.palette_combo.bind("<<ComboboxSelected>>", lambda e: self.schedule_convert())

        tk.Button(param, text="✏️ 编辑像素画", command=self.open_editor, width=12, bg="#FF9800", fg="white").pack(side=tk.LEFT)

        # ---- 预览区域 ----
        display = tk.Frame(main)
        display.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        left = tk.LabelFrame(display, text="📷 原图")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.orig_canvas = tk.Canvas(left, bg="#1e1e1e", highlightthickness=0)
        self.orig_canvas.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        right = tk.LabelFrame(display, text="🎨 像素画")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.res_canvas = tk.Canvas(right, bg="#1e1e1e", highlightthickness=0)
        self.res_canvas.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # 滚轮缩放 & 双击重置
        self.orig_canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.res_canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.orig_canvas.bind("<Double-Button-1>", self.reset_zoom)
        self.res_canvas.bind("<Double-Button-1>", self.reset_zoom)

        self.root.bind("<Configure>", self.on_resize)

        # ---- 底部 ----
        bottom = tk.Frame(main)
        bottom.pack(fill=tk.X, pady=(5, 0))

        self.save_btn = tk.Button(bottom, text="💾 保存像素画", command=self.save_image,
                                  state=tk.DISABLED, bg="#2196F3", fg="white")
        self.save_btn.pack(side=tk.LEFT, padx=(0, 8))

        # 缩放按钮（文字）
        tk.Button(bottom, text="放大", command=self.zoom_in, width=4, bg="#333", fg="white").pack(side=tk.LEFT, padx=(0, 2))
        tk.Button(bottom, text="缩小", command=self.zoom_out, width=4, bg="#333", fg="white").pack(side=tk.LEFT, padx=(0, 2))
        tk.Button(bottom, text="重置", command=self.reset_zoom, width=4, bg="#333", fg="white").pack(side=tk.LEFT, padx=(0, 5))

        self.zoom_label = tk.Label(bottom, text="100%", fg="#888", font=("Arial", 10))
        self.zoom_label.pack(side=tk.LEFT, padx=(5, 10))

        self.status = tk.Label(bottom, text="就绪", fg="blue", anchor="w")
        self.status.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        self.load_config()

    # ========== 缩放功能 ==========
    def on_mousewheel(self, event):
        delta = event.delta
        if delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor *= 0.9
        self.zoom_factor = max(0.1, min(10.0, self.zoom_factor))
        self.update_zoom_label()
        self.refresh_display()

    def zoom_in(self):
        self.zoom_factor = min(10.0, self.zoom_factor * 1.15)
        self.update_zoom_label()
        self.refresh_display()

    def zoom_out(self):
        self.zoom_factor = max(0.1, self.zoom_factor * 0.85)
        self.update_zoom_label()
        self.refresh_display()

    def reset_zoom(self, event=None):
        self.zoom_factor = 1.0
        self.update_zoom_label()
        self.refresh_display()

    def update_zoom_label(self):
        self.zoom_label.config(text=f"{int(self.zoom_factor * 100)}%")

    def refresh_display(self):
        if self.original_image:
            self.show_image(self.original_image, self.orig_canvas)
        if self.result_image:
            self.show_image(self.result_image, self.res_canvas)

    # ========== 加载单张图片 ==========
    def load_single_image(self):
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"), ("所有文件", "*.*")]
        )
        if path:
            self.is_batch_mode = False
            self.batch_images = []
            self.batch_index = 0
            self.update_nav_buttons()
            self.zoom_factor = 1.0
            self.update_zoom_label()
            self.load_image_path(path)

    # ========== 批量处理：加载文件夹 ==========
    def load_batch_folder(self):
        folder = filedialog.askdirectory(title="选择包含图片的文件夹")
        if not folder:
            return

        exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
        files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(exts)]
        
        if not files:
            messagebox.showinfo("提示", "该文件夹中没有找到图片文件")
            return

        self.batch_images = files
        self.batch_index = 0
        self.is_batch_mode = True
        self.file_label.config(text=f"📁 {os.path.basename(folder)} ({len(files)}张)")
        self.zoom_factor = 1.0
        self.update_zoom_label()
        self.update_nav_buttons()
        self.load_image_path(files[0])

    # ========== 翻页逻辑 ==========
    def prev_image(self):
        if self.batch_index > 0:
            self.batch_index -= 1
            self.zoom_factor = 1.0
            self.update_zoom_label()
            self.load_image_path(self.batch_images[self.batch_index])
            self.update_nav_buttons()

    def next_image(self):
        if self.batch_index < len(self.batch_images) - 1:
            self.batch_index += 1
            self.zoom_factor = 1.0
            self.update_zoom_label()
            self.load_image_path(self.batch_images[self.batch_index])
            self.update_nav_buttons()

    def update_nav_buttons(self):
        if self.is_batch_mode and self.batch_images:
            total = len(self.batch_images)
            self.prev_btn.config(state=tk.NORMAL if self.batch_index > 0 else tk.DISABLED)
            self.next_btn.config(state=tk.NORMAL if self.batch_index < total - 1 else tk.DISABLED)
            self.page_label.config(text=f"📄 {self.batch_index + 1} / {total}")
            self.save_batch_btn.config(state=tk.NORMAL)
        else:
            self.prev_btn.config(state=tk.DISABLED)
            self.next_btn.config(state=tk.DISABLED)
            self.page_label.config(text="")
            self.save_batch_btn.config(state=tk.DISABLED)

    def save_current_batch(self):
        if self.result_image is None:
            return
        current_path = self.batch_images[self.batch_index]
        folder = os.path.dirname(current_path)
        output_folder = os.path.join(folder, "pixel_output")
        os.makedirs(output_folder, exist_ok=True)
        base = os.path.splitext(os.path.basename(current_path))[0]
        save_path = os.path.join(output_folder, f"{base}_pixel.png")
        
        try:
            self.result_image.save(save_path)
            self.update_status(f"✅ 已保存：{os.path.basename(save_path)}")
        except Exception as e:
            messagebox.showerror("保存错误", str(e))

    # ========== 加载图片路径 ==========
    def load_image_path(self, path):
        try:
            self.original_image = Image.open(path).convert("RGBA")
            self.file_label.config(text=os.path.basename(path))
            self.result_image = None
            self.save_btn.config(state=tk.DISABLED)
            self.current_display_size = (0, 0)
            self.update_status(f"已加载：{os.path.basename(path)}，自动转换中...")
            self.show_image(self.original_image, self.orig_canvas)
            self.schedule_convert(immediate=True)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片：{e}")

    def on_drop(self, event):
        files = event.data.split()
        if files:
            path = files[0].strip('{}')
            if os.path.isfile(path):
                self.is_batch_mode = False
                self.batch_images = []
                self.batch_index = 0
                self.zoom_factor = 1.0
                self.update_zoom_label()
                self.update_nav_buttons()
                self.load_image_path(path)

    # ========== 预设尺寸 ==========
    def on_preset_selected(self, event):
        preset = self.preset_var.get()
        if preset == "自定义":
            return
        if self.original_image is None:
            messagebox.showwarning("提示", "请先加载图片")
            self.preset_var.set("自定义")
            return

        target_w, target_h = PRESETS[preset]
        w, h = self.original_image.size
        block_w = w // target_w
        block_h = h // target_h
        new_block = min(block_w, block_h, 40)

        if new_block < 2:
            messagebox.showwarning("提示", f"图片太小，无法生成 {preset} 的网格")
            self.preset_var.set("自定义")
            return

        self.block_var.set(max(2, new_block))
        self.block_label.config(text=str(self.block_var.get()))
        self.schedule_convert(immediate=True)
        self.update_status(f"预设 {preset}，块大小 {self.block_var.get()}")

    def on_block_changed(self):
        if self.preset_var.get() != "自定义":
            self.preset_var.set("自定义")
        self.schedule_convert()

    # ========== 核心处理 ==========
    def process_image(self, img, block, colors, palette):
        w, h = img.size
        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            rgb_img = Image.merge('RGB', (r, g, b))
            has_alpha = True
        else:
            rgb_img = img.convert('RGB')
            has_alpha = False

        bw = max(1, w // block)
        bh = max(1, h // block)

        small = rgb_img.resize((bw, bh), Image.NEAREST)

        if palette:
            small = self.apply_palette(small, palette)
        else:
            if colors < 256:
                small = small.quantize(colors=colors, method=Image.MEDIANCUT)
                small = small.convert('RGB')

        result_rgb = small.resize((w, h), Image.NEAREST)

        if has_alpha:
            small_a = a.resize((bw, bh), Image.NEAREST)
            result_a = small_a.resize((w, h), Image.NEAREST)
            result = Image.merge('RGBA', (*result_rgb.split(), result_a))
        else:
            result = result_rgb

        self.grid_w = bw
        self.grid_h = bh
        self.grid_colors = []
        small_pixels = small.load()
        for y in range(bh):
            row = []
            for x in range(bw):
                row.append(small_pixels[x, y])
            self.grid_colors.append(row)

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

    # ========== 转换调度 ==========
    def schedule_convert(self, immediate=False):
        if self.original_image is None:
            return
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if immediate:
            self.do_convert()
        else:
            self.after_id = self.root.after(200, self.do_convert)

    def do_convert(self):
        if self.original_image is None:
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
            self.update_status(f"✅ 块 {block} | 颜色 {colors} | 网格 {self.grid_w}×{self.grid_h}")
        except Exception as e:
            messagebox.showerror("转换错误", str(e))

    # ========== 显示图片（支持缩放） ==========
    def show_image(self, pil_img, canvas):
        if pil_img is None:
            return
        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        if cw < 10 or ch < 10:
            return

        w, h = pil_img.size
        scale_fit = min(cw / w, ch / h, 1.0)
        final_scale = scale_fit * self.zoom_factor
        new_w = int(w * final_scale)
        new_h = int(h * final_scale)

        if new_w < 1 or new_h < 1:
            return

        resized = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized)
        canvas.delete("all")
        x = (cw - new_w) // 2
        y = (ch - new_h) // 2
        canvas.create_image(x, y, anchor=tk.NW, image=tk_img)

        if canvas == self.orig_canvas:
            self.orig_tk = tk_img
        else:
            self.res_tk = tk_img

    def on_resize(self, event):
        if self.original_image is None:
            return
        w = self.orig_canvas.winfo_width()
        h = self.orig_canvas.winfo_height()
        if w > 10 and h > 10 and (w, h) != self.current_display_size:
            self.current_display_size = (w, h)
            self.refresh_display()

    # ========== 像素画编辑器 ==========
    def open_editor(self):
        if self.result_image is None:
            messagebox.showwarning("提示", "请先生成像素画")
            return

        if self.edit_window is not None and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return

        self.edit_window = tk.Toplevel(self.root)
        self.edit_window.title("✏️ 像素画编辑器")
        self.edit_window.geometry("700x600")
        self.edit_window.minsize(500, 400)

        self.undo_stack = []
        self.redo_stack = []
        self.edit_tool = "brush"
        self.current_color = (255, 0, 0)

        grid_data = self.grid_colors
        grid_h = len(grid_data)
        grid_w = len(grid_data[0]) if grid_h > 0 else 0
        self.edit_grid_w = grid_w
        self.edit_grid_h = grid_h
        self.edit_grid = [row[:] for row in grid_data]

        top_frame = tk.Frame(self.edit_window)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(top_frame, text="工具:").pack(side=tk.LEFT)
        self.tool_var = tk.StringVar(value="画笔")
        tk.Radiobutton(top_frame, text="🖊️ 画笔", variable=self.tool_var, value="画笔", command=self.set_tool).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(top_frame, text="🧹 橡皮", variable=self.tool_var, value="橡皮", command=self.set_tool).pack(side=tk.LEFT, padx=5)

        tk.Label(top_frame, text="  ").pack(side=tk.LEFT)

        self.color_preview = tk.Canvas(top_frame, width=30, height=30, bg="#FF0000", highlightthickness=2)
        self.color_preview.pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="选择颜色", command=self.choose_color).pack(side=tk.LEFT, padx=5)

        tk.Label(top_frame, text="  ").pack(side=tk.LEFT)

        tk.Button(top_frame, text="↩ 撤销", command=self.editor_undo).pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="↪ 重做", command=self.editor_redo).pack(side=tk.LEFT, padx=2)

        tk.Button(top_frame, text="✅ 保存并关闭", command=self.save_editor).pack(side=tk.RIGHT, padx=5)

        canvas_frame = tk.Frame(self.edit_window)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.edit_canvas = tk.Canvas(canvas_frame, bg="#1e1e1e", highlightthickness=0)
        self.edit_canvas.pack(fill=tk.BOTH, expand=True)

        self.edit_canvas.bind("<Configure>", self.draw_edit_grid)
        self.edit_canvas.bind("<Button-1>", self.on_edit_click)
        self.edit_canvas.bind("<B1-Motion>", self.on_edit_drag)

        self.draw_edit_grid()

    def set_tool(self):
        self.edit_tool = "eraser" if self.tool_var.get() == "橡皮" else "brush"

    def choose_color(self):
        color = colorchooser.askcolor(title="选择颜色", initialcolor=self.current_color)
        if color and color[0]:
            self.current_color = tuple(int(c) for c in color[0])
            self.color_preview.config(bg=f"#{self.current_color[0]:02x}{self.current_color[1]:02x}{self.current_color[2]:02x}")

    def draw_edit_grid(self, event=None):
        if self.edit_grid_w == 0 or self.edit_grid_h == 0:
            return
        cw = self.edit_canvas.winfo_width()
        ch = self.edit_canvas.winfo_height()
        if cw < 10 or ch < 10:
            return

        cell_w = cw / self.edit_grid_w
        cell_h = ch / self.edit_grid_h
        cell_size = min(cell_w, cell_h)
        offset_x = (cw - cell_size * self.edit_grid_w) / 2
        offset_y = (ch - cell_size * self.edit_grid_h) / 2

        self.edit_cell_size = cell_size
        self.edit_offset_x = offset_x
        self.edit_offset_y = offset_y

        self.edit_canvas.delete("all")

        for y in range(self.edit_grid_h):
            for x in range(self.edit_grid_w):
                color = self.edit_grid[y][x]
                x0 = offset_x + x * cell_size
                y0 = offset_y + y * cell_size
                hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                self.edit_canvas.create_rectangle(
                    x0, y0, x0 + cell_size, y0 + cell_size,
                    fill=hex_color, outline="#333", width=1,
                    tags=f"cell_{y}_{x}"
                )

    def on_edit_click(self, event):
        self.edit_pixel_at(event.x, event.y)

    def on_edit_drag(self, event):
        self.edit_pixel_at(event.x, event.y)

    def edit_pixel_at(self, x, y):
        if self.edit_grid_w == 0 or self.edit_grid_h == 0:
            return
        rel_x = x - self.edit_offset_x
        rel_y = y - self.edit_offset_y
        if rel_x < 0 or rel_y < 0:
            return
        grid_x = int(rel_x / self.edit_cell_size)
        grid_y = int(rel_y / self.edit_cell_size)
        if grid_x >= self.edit_grid_w or grid_y >= self.edit_grid_h:
            return

        if not self.undo_stack or self.undo_stack[-1] != (grid_x, grid_y, self.edit_grid[grid_y][grid_x]):
            self.undo_stack.append((grid_x, grid_y, self.edit_grid[grid_y][grid_x]))
            self.redo_stack = []

        if self.edit_tool == "eraser":
            color = (128, 128, 128)
        else:
            color = self.current_color

        self.edit_grid[grid_y][grid_x] = color

        x0 = self.edit_offset_x + grid_x * self.edit_cell_size
        y0 = self.edit_offset_y + grid_y * self.edit_cell_size
        hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        self.edit_canvas.create_rectangle(
            x0, y0, x0 + self.edit_cell_size, y0 + self.edit_cell_size,
            fill=hex_color, outline="#333", width=1,
            tags=f"cell_{grid_y}_{grid_x}"
        )

    def editor_undo(self):
        if not self.undo_stack:
            return
        grid_x, grid_y, old_color = self.undo_stack.pop()
        self.redo_stack.append((grid_x, grid_y, self.edit_grid[grid_y][grid_x]))
        self.edit_grid[grid_y][grid_x] = old_color
        self.draw_edit_grid()

    def editor_redo(self):
        if not self.redo_stack:
            return
        grid_x, grid_y, new_color = self.redo_stack.pop()
        self.undo_stack.append((grid_x, grid_y, self.edit_grid[grid_y][grid_x]))
        self.edit_grid[grid_y][grid_x] = new_color
        self.draw_edit_grid()

    def save_editor(self):
        if self.edit_grid_w == 0 or self.edit_grid_h == 0:
            return
        small_img = Image.new('RGB', (self.edit_grid_w, self.edit_grid_h))
        pixels = small_img.load()
        for y in range(self.edit_grid_h):
            for x in range(self.edit_grid_w):
                pixels[x, y] = self.edit_grid[y][x]

        if self.result_image:
            w, h = self.result_image.size
            new_result = small_img.resize((w, h), Image.NEAREST)
            if self.result_image.mode == 'RGBA':
                r, g, b = new_result.split()
                _, _, _, a = self.result_image.split()
                new_result = Image.merge('RGBA', (r, g, b, a))
            self.result_image = new_result
            self.show_image(new_result, self.res_canvas)
            self.update_status("✅ 编辑已应用")

        self.edit_window.destroy()
        self.edit_window = None

    # ========== 保存图片 ==========
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

    # ========== 配置 ==========
    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), "pixelcraft_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                self.block_var.set(config.get("block_size", 12))
                self.color_var.set(config.get("colors", 16))
                self.block_label.config(text=str(self.block_var.get()))
                self.color_label.config(text=str(self.color_var.get()))
            except:
                pass

    def save_config(self):
        config = {
            "block_size": self.block_var.get(),
            "colors": self.color_var.get(),
        }
        try:
            config_path = os.path.join(os.path.dirname(__file__), "pixelcraft_config.json")
            with open(config_path, 'w') as f:
                json.dump(config, f)
        except:
            pass

    def update_status(self, msg):
        self.status.config(text=msg)


# ========== 启动 ==========
if __name__ == "__main__":
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = PixelCraft(root)
    root.mainloop()