import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageDraw, ImageTk, ImagePalette
import os
import threading
import json
import tkinter.font as tkFont
from collections import Counter, deque
import math
import time
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor

try:
    from tkinterdnd2 import TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("提示：未安装 tkinterdnd2，拖拽功能不可用。安装：pip install tkinterdnd2")


def get_base_dir():
    """获取项目根目录（src/ 的父目录）"""
    return os.path.dirname(os.path.dirname(__file__))


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
    "Commodore 64 (16色)": [
        (0,0,0), (255,255,255), (136,0,0), (170,255,238),
        (204,68,204), (0,204,85), (0,0,170), (238,238,119),
        (221,136,85), (102,68,0), (255,119,119), (51,51,51),
        (119,119,119), (170,255,102), (0,68,204), (187,85,0)
    ],
    "ZX Spectrum (15色)": [
        (0,0,0), (0,0,192), (0,192,0), (0,192,192),
        (192,0,0), (192,0,192), (192,192,0), (192,192,192),
        (0,0,255), (0,255,0), (0,255,255), (255,0,0),
        (255,0,255), (255,255,0), (255,255,255)
    ],
    "Atari 2600 (8色)": [
        (0,0,0), (255,255,255), (255,0,0), (0,255,0),
        (0,0,255), (255,255,0), (255,0,255), (0,255,255)
    ],
    "PICO-8 (16色)": [
        (0,0,0), (29,43,83), (126,37,83), (0,135,81),
        (171,82,54), (95,87,79), (194,195,199), (255,241,232),
        (255,0,77), (255,163,0), (255,236,39), (0,228,54),
        (41,173,255), (131,118,156), (255,119,168), (255,204,170)
    ]
}

PRESETS = {
    "16×16": (16, 16),
    "32×32": (32, 32),
    "48×48": (48, 48),
    "64×64": (64, 64),
    "128×128": (128, 128),
}

# 调色板缓存
_palette_cache = {}

def get_palette_image(colors):
    if not colors:
        return None
    key = tuple(colors)
    if key in _palette_cache:
        return _palette_cache[key]
    palette_img = Image.new('P', (1, len(colors)))
    palette_img.putdata(list(range(len(colors))))
    palette = []
    for c in colors:
        palette.extend(c)
    palette_img.putpalette(palette)
    _palette_cache[key] = palette_img
    return palette_img


class PixelCraft:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 PixelCraft")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)

        self.original_image = None
        self.result_image = None
        self.orig_tk = None
        self.res_tk = None
        self.current_display_size = (0, 0)
        self.after_id = None
        self.zoom_factor = 1.0

        self.batch_images = []
        self.batch_index = 0
        self.is_batch_mode = False

        self.compare_window = None

        self.edit_window = None
        self.grid_colors = []
        self.grid_w = 0
        self.grid_h = 0
        self.undo_stack = []
        self.redo_stack = []
        self.current_color = (255, 0, 0)
        self.edit_tool = "brush"

        self.edit_selection = []
        self.edit_selection_start = None
        self.selection_rect_id = None
        self.edit_clipboard = []

        self.pan_data = None
        self.main_frame = None

        # 缓存
        self._cached_orig_display = None
        self._cached_res_display = None
        self._cached_zoom = -1

        if HAS_DND and isinstance(root, TkinterDnD.Tk):
            root.drop_target_register('DND_Files')
            root.dnd_bind('<<Drop>>', self.on_drop)

        self.setup_ui()
        self.load_config()
        self.update_status("拖拽图片或点击「选择图片」开始")

    def restart_app(self):
        self.save_config()
        self.root.quit()
        self.root.destroy()
        if getattr(sys, 'frozen', False):
            subprocess.Popen([sys.executable] + sys.argv)
        else:
            subprocess.Popen([sys.executable, sys.argv[0]])
        sys.exit(0)

    def setup_ui(self):
        if self.main_frame:
            self.main_frame.destroy()
            self.main_frame = None

        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # ---- 文件菜单 ----
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="保存", command=self.save_image)
        file_menu.add_command(label="另存为", command=self.save_image_as)
        file_menu.add_command(label="全部保存", command=self.save_all)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # ---- 编辑菜单 ----
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="编辑像素画", command=self.open_editor)
        edit_menu.add_command(label="重置缩放", command=self.reset_zoom)

        preset_sub = tk.Menu(edit_menu, tearoff=0)
        edit_menu.add_cascade(label="预设尺寸", menu=preset_sub)
        for name in PRESETS.keys():
            preset_sub.add_command(label=name, command=lambda n=name: self.apply_preset(n))

        palette_sub = tk.Menu(edit_menu, tearoff=0)
        edit_menu.add_cascade(label="色盘", menu=palette_sub)
        for name in PALETTES.keys():
            palette_sub.add_command(label=name, command=lambda n=name: self.switch_palette(n))

        # ---- 帮助菜单 ----
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)

        # ---- 主框架 ----
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=8, fill=tk.BOTH, expand=True)

        # ---- 文件选择行 ----
        file_row = tk.Frame(self.main_frame)
        file_row.pack(fill=tk.X, pady=(0, 5))

        tk.Button(file_row, text="📂 选择图片", command=self.load_single_image, width=12).pack(side=tk.LEFT, padx=(0,5))
        tk.Button(file_row, text="📁 批量处理", command=self.load_batch_folder, width=12).pack(side=tk.LEFT, padx=(0,5))
        self.file_label = tk.Label(file_row, text="未选择文件", anchor="w", relief="sunken")
        self.file_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # ---- 翻页行 ----
        nav_frame = tk.Frame(self.main_frame)
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
        param = tk.Frame(self.main_frame)
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
        self.block_scale.bind("<MouseWheel>", lambda e: self.on_scale_wheel(e, self.block_scale, self.block_var, self.block_label, self.on_block_changed))
        self.block_label = tk.Label(param, text="12", width=3)
        self.block_label.pack(side=tk.LEFT, padx=(0, 10))
        self.block_scale.config(command=lambda v: (self.block_label.config(text=v), self.on_block_changed()))

        tk.Label(param, text="颜色:").pack(side=tk.LEFT)
        self.color_var = tk.IntVar(value=16)
        self.color_scale = tk.Scale(param, from_=2, to=64, orient=tk.HORIZONTAL,
                                    variable=self.color_var, length=100, showvalue=0)
        self.color_scale.pack(side=tk.LEFT, padx=(0, 5))
        self.color_scale.bind("<MouseWheel>", lambda e: self.on_scale_wheel(e, self.color_scale, self.color_var, self.color_label, self.on_block_changed))
        self.color_label = tk.Label(param, text="16", width=3)
        self.color_label.pack(side=tk.LEFT, padx=(0, 10))
        self.color_scale.config(command=lambda v: (self.color_label.config(text=v), self.on_block_changed()))

        tk.Label(param, text="色盘:").pack(side=tk.LEFT)
        self.palette_var = tk.StringVar(value="自动")
        self.palette_combo = ttk.Combobox(param, textvariable=self.palette_var,
                                          values=list(PALETTES.keys()), state="readonly", width=18)
        self.palette_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.palette_combo.bind("<<ComboboxSelected>>", lambda e: self.schedule_convert())

        tk.Button(param, text="✏️ 编辑像素画", command=self.open_editor, width=12, bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(param, text="🔍 对比视图", command=self.open_comparison, width=12, bg="#9C27B0", fg="white").pack(side=tk.LEFT)

        # ---- 预览区域 ----
        display = tk.Frame(self.main_frame)
        display.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        display.grid_rowconfigure(0, weight=1)
        display.grid_columnconfigure(0, weight=1, uniform="preview")
        display.grid_columnconfigure(1, weight=1, uniform="preview")

        left = tk.LabelFrame(display, text="📷 原图")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self._setup_canvas_with_scrollbar(left, "orig")

        right = tk.LabelFrame(display, text="🎨 像素画")
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self._setup_canvas_with_scrollbar(right, "res")

        self.orig_canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.res_canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.orig_canvas.bind("<Double-Button-1>", self.reset_zoom)
        self.res_canvas.bind("<Double-Button-1>", self.reset_zoom)

        self.orig_canvas.bind("<ButtonPress-1>", lambda e: self._start_pan(e, "orig"))
        self.orig_canvas.bind("<B1-Motion>", self._do_pan)
        self.orig_canvas.bind("<ButtonRelease-1>", self._end_pan)
        self.res_canvas.bind("<ButtonPress-1>", lambda e: self._start_pan(e, "res"))
        self.res_canvas.bind("<B1-Motion>", self._do_pan)
        self.res_canvas.bind("<ButtonRelease-1>", self._end_pan)

        self.root.bind("<Configure>", self.on_resize)

        # ---- 底部 ----
        bottom = tk.Frame(self.main_frame)
        bottom.pack(fill=tk.X, pady=(5, 0))

        self.save_btn = tk.Button(bottom, text="💾 保存像素画", command=self.save_image,
                                  state=tk.DISABLED, bg="#2196F3", fg="white")
        self.save_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.svg_btn = tk.Button(bottom, text="📐 导出 SVG", command=self.export_svg,
                                 state=tk.DISABLED, bg="#9C27B0", fg="white")
        self.svg_btn.pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(bottom, text="放大", command=self.zoom_in, width=4, bg="#333", fg="white").pack(side=tk.LEFT, padx=(0, 2))
        tk.Button(bottom, text="缩小", command=self.zoom_out, width=4, bg="#333", fg="white").pack(side=tk.LEFT, padx=(0, 2))
        tk.Button(bottom, text="重置", command=self.reset_zoom, width=4, bg="#333", fg="white").pack(side=tk.LEFT, padx=(0, 5))

        self.zoom_label = tk.Label(bottom, text="100%", fg="#888", font=("Arial", 10))
        self.zoom_label.pack(side=tk.LEFT, padx=(5, 10))

        self.status = tk.Label(bottom, text="", fg="blue", anchor="w")
        self.status.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

    def _setup_canvas_with_scrollbar(self, parent, name):
        frame = tk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        v_scroll = tk.Scrollbar(frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        h_scroll = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        canvas = tk.Canvas(frame, bg="#1e1e1e", highlightthickness=0,
                           xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if name == "orig":
            self.orig_canvas = canvas
            self.orig_v_scroll = v_scroll
            self.orig_h_scroll = h_scroll
            v_scroll.config(command=self._sync_scroll_orig_v)
            h_scroll.config(command=self._sync_scroll_orig_h)
        else:
            self.res_canvas = canvas
            self.res_v_scroll = v_scroll
            self.res_h_scroll = h_scroll
            v_scroll.config(command=self._sync_scroll_res_v)
            h_scroll.config(command=self._sync_scroll_res_h)

    def _sync_scroll_orig_v(self, *args):
        self.orig_canvas.yview(*args)
        if self.result_image:
            self.res_canvas.yview(*args)

    def _sync_scroll_orig_h(self, *args):
        self.orig_canvas.xview(*args)
        if self.result_image:
            self.res_canvas.xview(*args)

    def _sync_scroll_res_v(self, *args):
        self.res_canvas.yview(*args)
        if self.original_image:
            self.orig_canvas.yview(*args)

    def _sync_scroll_res_h(self, *args):
        self.res_canvas.xview(*args)
        if self.original_image:
            self.orig_canvas.xview(*args)

    def _start_pan(self, event, target):
        self.pan_data = {"x": event.x, "y": event.y, "xview": self.orig_canvas.xview()[0], "yview": self.orig_canvas.yview()[0]}

    def _do_pan(self, event):
        if self.pan_data is None:
            return
        x0, y0 = self.pan_data["xview"], self.pan_data["yview"]
        dx, dy = event.x - self.pan_data["x"], event.y - self.pan_data["y"]
        bbox = self.orig_canvas.bbox("all")
        if not bbox:
            return
        rw, rh = bbox[2]-bbox[0], bbox[3]-bbox[1]
        vw, vh = self.orig_canvas.winfo_width(), self.orig_canvas.winfo_height()
        if rw == 0 or rh == 0:
            return
        nx = max(0, min(1, x0 + (dx / (rw - vw) if rw > vw else 0)))
        ny = max(0, min(1, y0 + (dy / (rh - vh) if rh > vh else 0)))
        self.orig_canvas.xview_moveto(nx)
        self.orig_canvas.yview_moveto(ny)
        self.res_canvas.xview_moveto(nx)
        self.res_canvas.yview_moveto(ny)
        self.pan_data["xview"], self.pan_data["yview"] = nx, ny
        self.pan_data["x"], self.pan_data["y"] = event.x, event.y

    def _end_pan(self, event):
        self.pan_data = None

    def on_scale_wheel(self, event, scale_widget, var, label, callback):
        delta = 1 if event.delta > 0 else -1
        new_val = var.get() + delta
        from_val = int(scale_widget.cget("from"))
        to_val = int(scale_widget.cget("to"))
        new_val = max(from_val, min(to_val, new_val))
        var.set(new_val)
        label.config(text=str(new_val))
        callback()
        return "break"

    def on_mousewheel(self, event):
        self.zoom_factor *= 1.1 if event.delta > 0 else 0.9
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
        self._cached_zoom = -1
        self.refresh_display()

    def update_zoom_label(self):
        self.zoom_label.config(text=f"{int(self.zoom_factor * 100)}%")

    def refresh_display(self):
        self._cached_orig_display = None
        self._cached_res_display = None
        if self.original_image:
            self.show_image(self.original_image, "orig")
        if self.result_image:
            self.show_image(self.result_image, "res")

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
            self._cached_zoom = -1
            self.load_image_path(path)

    def load_image_path(self, path):
        try:
            self.original_image = Image.open(path).convert("RGBA")
            self.file_label.config(text=os.path.basename(path))
            self.result_image = None
            self.save_btn.config(state=tk.DISABLED)
            self.svg_btn.config(state=tk.DISABLED)
            self.current_display_size = (0, 0)
            self._cached_orig_display = None
            self._cached_res_display = None
            self.update_status(f"已加载：{os.path.basename(path)}，自动转换中...")
            self.show_image(self.original_image, "orig")
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
                self._cached_zoom = -1
                self.update_nav_buttons()
                self.load_image_path(path)

    def load_batch_folder(self):
        folder = filedialog.askdirectory(title="选择包含图片的文件夹")
        if not folder:
            return

        # 加载进度窗口
        progress_win = tk.Toplevel(self.root)
        progress_win.title("加载中")
        progress_win.geometry("300x80")
        progress_win.resizable(False, False)
        progress_win.transient(self.root)
        progress_win.grab_set()
        tk.Label(progress_win, text="正在扫描图片...", font=("Arial", 12)).pack(pady=15)
        progress_bar = ttk.Progressbar(progress_win, length=250, mode='indeterminate')
        progress_bar.pack(pady=5)
        progress_bar.start()
        progress_win.update()

        exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
        files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(exts)]

        progress_bar.stop()
        progress_win.destroy()

        if not files:
            messagebox.showinfo("提示", "该文件夹中没有找到图片文件")
            return

        self.batch_images = files
        self.batch_index = 0
        self.is_batch_mode = True
        self.file_label.config(text=f"📁 {os.path.basename(folder)} ({len(files)}张)")
        self.zoom_factor = 1.0
        self.update_zoom_label()
        self._cached_zoom = -1
        self.update_nav_buttons()
        self.load_image_path(files[0])
        self.update_status(f"已加载 {len(files)} 张图片，请翻页浏览或调整参数")

    def prev_image(self):
        if self.batch_index > 0:
            self.batch_index -= 1
            self.zoom_factor = 1.0
            self.update_zoom_label()
            self._cached_zoom = -1
            self.load_image_path(self.batch_images[self.batch_index])
            self.update_nav_buttons()

    def next_image(self):
        if self.batch_index < len(self.batch_images)-1:
            self.batch_index += 1
            self.zoom_factor = 1.0
            self.update_zoom_label()
            self._cached_zoom = -1
            self.load_image_path(self.batch_images[self.batch_index])
            self.update_nav_buttons()

    def update_nav_buttons(self):
        if self.is_batch_mode and self.batch_images:
            total = len(self.batch_images)
            self.prev_btn.config(state=tk.NORMAL if self.batch_index>0 else tk.DISABLED)
            self.next_btn.config(state=tk.NORMAL if self.batch_index<total-1 else tk.DISABLED)
            self.page_label.config(text=f"📄 {self.batch_index+1} / {total}")
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
            self.update_status(f"已保存：{os.path.basename(save_path)}")
        except Exception as e:
            messagebox.showerror("保存错误", str(e))

    def apply_preset(self, preset_name):
        if self.original_image is None:
            messagebox.showwarning("提示", "请先加载图片")
            return
        self.preset_var.set(preset_name)
        self.on_preset_selected(None)

    def on_preset_selected(self, event):
        preset = self.preset_var.get()
        if preset == "自定义" or self.original_image is None:
            return
        target_w, target_h = PRESETS[preset]
        w, h = self.original_image.size
        new_block = min(w//target_w, h//target_h, 40)
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

    def switch_palette(self, palette_name):
        if self.original_image is None:
            messagebox.showwarning("提示", "请先加载图片")
            return
        self.palette_var.set(palette_name)
        self.schedule_convert(immediate=True)

    def process_image(self, img, block, colors, palette, save_editor=True):
        w, h = img.size
        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            rgb_img = Image.merge('RGB', (r, g, b))
            has_alpha = True
        else:
            rgb_img = img.convert('RGB')
            has_alpha = False

        bw, bh = max(1, w//block), max(1, h//block)
        small = rgb_img.resize((bw, bh), Image.NEAREST)

        if palette:
            palette_img = get_palette_image(palette)
            if palette_img:
                small = small.quantize(palette=palette_img, dither=Image.NONE).convert('RGB')
            else:
                small = self._apply_palette_fallback(small, palette)
        else:
            if colors < 256:
                small = small.quantize(colors=colors, method=Image.MEDIANCUT).convert('RGB')

        result_rgb = small.resize((w, h), Image.NEAREST)

        if has_alpha:
            small_a = a.resize((bw, bh), Image.NEAREST)
            result_a = small_a.resize((w, h), Image.NEAREST)
            result = Image.merge('RGBA', (*result_rgb.split(), result_a))
        else:
            result = result_rgb

        if save_editor:
            self.grid_w, self.grid_h = bw, bh
            small_pixels = small.load()
            self.grid_colors = [[small_pixels[x, y] for x in range(bw)] for y in range(bh)]
        return result

    def _apply_palette_fallback(self, image, palette_colors):
        pixels = image.load()
        w, h = image.size
        for y in range(h):
            for x in range(w):
                r, g, b = pixels[x, y]
                best = min(palette_colors, key=lambda c: (r-c[0])**2 + (g-c[1])**2 + (b-c[2])**2)
                pixels[x, y] = best
        return image

    def schedule_convert(self, immediate=False):
        if self.original_image is None:
            return
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if immediate:
            self.do_convert()
        else:
            self.after_id = self.root.after(150, self.do_convert)

    def do_convert(self):
        if self.original_image is None:
            return
        block, colors = self.block_var.get(), self.color_var.get()
        palette = PALETTES.get(self.palette_var.get())
        try:
            img = self.original_image.copy()
            result = self.process_image(img, block, colors, palette)
            self.result_image = result
            self._cached_res_display = None
            self.show_image(result, "res")
            self.save_btn.config(state=tk.NORMAL)
            self.svg_btn.config(state=tk.NORMAL)
            self.update_status(f"✅ 块 {block} | 颜色 {colors} | 网格 {self.grid_w}×{self.grid_h}")
        except Exception as e:
            messagebox.showerror("转换错误", str(e))

    def show_image(self, pil_img, target):
        if pil_img is None:
            return
        canvas = self.orig_canvas if target == "orig" else self.res_canvas
        cw, ch = canvas.winfo_width(), canvas.winfo_height()
        if cw < 10 or ch < 10:
            self.root.after(50, lambda: self.show_image(pil_img, target))
            return

        w, h = pil_img.size
        scale_fit = min(cw / w, ch / h, 1.0) if (cw > 0 and ch > 0) else 1.0
        final_scale = scale_fit * self.zoom_factor
        new_w, new_h = int(w * final_scale), int(h * final_scale)
        if new_w < 1 or new_h < 1:
            return

        if target == "orig":
            if self._cached_orig_display and self._cached_orig_display[1] == (new_w, new_h):
                canvas.delete("all")
                canvas.create_image((cw - new_w)//2, (ch - new_h)//2, anchor=tk.NW, image=self._cached_orig_display[0])
                canvas.config(scrollregion=(0, 0, new_w, new_h))
                return
        else:
            if self._cached_res_display and self._cached_res_display[1] == (new_w, new_h):
                canvas.delete("all")
                canvas.create_image((cw - new_w)//2, (ch - new_h)//2, anchor=tk.NW, image=self._cached_res_display[0])
                canvas.config(scrollregion=(0, 0, new_w, new_h))
                return

        resized = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized)
        canvas.delete("all")
        if new_w <= cw and new_h <= ch:
            x, y = (cw - new_w)//2, (ch - new_h)//2
            canvas.create_image(x, y, anchor=tk.NW, image=tk_img)
            canvas.config(scrollregion=(0, 0, new_w, new_h))
        else:
            canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
            canvas.config(scrollregion=(0, 0, new_w, new_h))

        if target == "orig":
            self._cached_orig_display = (tk_img, (new_w, new_h))
        else:
            self._cached_res_display = (tk_img, (new_w, new_h))

        if new_w <= cw and new_h <= ch:
            canvas.xview_moveto(0)
            canvas.yview_moveto(0)

    def on_resize(self, event):
        if self.original_image is None:
            return
        w, h = self.orig_canvas.winfo_width(), self.orig_canvas.winfo_height()
        if w > 10 and h > 10 and (w, h) != self.current_display_size:
            self.current_display_size = (w, h)
            self._cached_orig_display = None
            self._cached_res_display = None
            self.refresh_display()

    def open_comparison(self):
        if self.original_image is None or self.result_image is None:
            messagebox.showwarning("提示", "请先生成像素画")
            return
        if self.compare_window is not None and self.compare_window.winfo_exists():
            self.compare_window.lift()
            return
        self.compare_window = tk.Toplevel(self.root)
        self.compare_window.title("🔍 对比视图")
        self.compare_window.geometry("900x600")
        self.compare_window.minsize(600, 400)
        orig = self.original_image.convert('RGB')
        res = self.result_image.convert('RGB')
        split_pos = 0.5
        dragging = False

        canvas_frame = tk.Frame(self.compare_window)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        compare_canvas = tk.Canvas(canvas_frame, bg="#1e1e1e", highlightthickness=0)
        compare_canvas.pack(fill=tk.BOTH, expand=True)

        def draw():
            cw, ch = compare_canvas.winfo_width(), compare_canvas.winfo_height()
            if cw < 10 or ch < 10:
                compare_canvas.after(50, draw)
                return
            w, h = orig.size
            scale = min(cw / w, ch / h, 1.0)
            nw, nh = int(w * scale), int(h * scale)
            orig_r = orig.resize((nw, nh), Image.Resampling.LANCZOS)
            res_r = res.resize((nw, nh), Image.Resampling.LANCZOS)
            self.compare_orig_tk = ImageTk.PhotoImage(orig_r)
            self.compare_res_tk = ImageTk.PhotoImage(res_r)
            compare_canvas.delete("all")
            xoff, yoff = (cw - nw)//2, (ch - nh)//2
            compare_canvas.create_image(xoff, yoff, anchor=tk.NW, image=self.compare_orig_tk)
            split_x = int(max(0, min(nw, split_pos * nw)))
            compare_canvas.create_rectangle(xoff + split_x, yoff, xoff + nw, yoff + nh, fill="", outline="", tags="clip")
            compare_canvas.create_image(xoff + split_x, yoff, anchor=tk.NW, image=self.compare_res_tk, tags="res")
            compare_canvas.tag_clip("res", xoff + split_x, yoff, xoff + nw, yoff + nh)
            compare_canvas.create_line(xoff + split_x, yoff, xoff + split_x, yoff + nh, fill="white", width=2, tags="line")
            r = 10
            compare_canvas.create_oval(xoff + split_x - r, yoff + nh//2 - r,
                                       xoff + split_x + r, yoff + nh//2 + r,
                                       fill="white", outline="#2196F3", width=2, tags="handle")
            compare_canvas.create_text(xoff + split_x, yoff + 20,
                                       text=f"{int(split_pos * 100)}%", fill="white",
                                       font=("Arial", 12, "bold"), tags="label")
            compare_canvas.compare_xoff = xoff
            compare_canvas.compare_nw = nw

        def on_down(e):
            nonlocal dragging
            split_x = int(split_pos * compare_canvas.compare_nw) + compare_canvas.compare_xoff
            if abs(e.x - split_x) < 25:
                dragging = True

        def on_move(e):
            nonlocal dragging, split_pos
            if not dragging:
                return
            rel = e.x - compare_canvas.compare_xoff
            nw = compare_canvas.compare_nw
            split_pos = max(0.02, min(0.98, rel / nw))
            draw()

        def on_up(e):
            nonlocal dragging
            dragging = False

        compare_canvas.bind("<Button-1>", on_down)
        compare_canvas.bind("<B1-Motion>", on_move)
        compare_canvas.bind("<ButtonRelease-1>", on_up)
        compare_canvas.bind("<Configure>", lambda e: draw())

        sep = ttk.Separator(self.compare_window, orient='horizontal')
        sep.pack(fill=tk.X, padx=10)

        bottom_frame = tk.Frame(self.compare_window)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(bottom_frame, text="← 原图", fg="#888").pack(side=tk.LEFT, padx=(0, 10))
        slider = tk.Scale(bottom_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=400)
        slider.set(50)
        slider.pack(side=tk.LEFT, padx=10)

        def slider_update(val):
            nonlocal split_pos
            split_pos = float(val) / 100
            draw()
        slider.config(command=slider_update)
        tk.Label(bottom_frame, text="像素画 →", fg="#888").pack(side=tk.LEFT, padx=(10, 0))
        tk.Button(bottom_frame, text="重置", command=lambda: (slider.set(50), slider_update("50")),
                  width=6, bg="#333", fg="white").pack(side=tk.RIGHT, padx=(0, 5))
        tk.Button(bottom_frame, text="关闭", command=self.compare_window.destroy,
                  width=6, bg="#555", fg="white").pack(side=tk.RIGHT)

        self.compare_window.after(100, draw)

    def export_svg(self):
        if self.result_image is None:
            messagebox.showwarning("提示", "请先生成像素画")
            return
        path = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("SVG矢量图", "*.svg")])
        if not path:
            return
        try:
            img = self.result_image.convert('RGB')
            w, h = img.size
            pixels = img.load()
            ps = 10
            svg = f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{w*ps}" height="{h*ps}" viewBox="0 0 {w*ps} {h*ps}">\n  <rect width="100%" height="100%" fill="#ffffff"/>\n'
            for y in range(h):
                for x in range(w):
                    r, g, b = pixels[x, y]
                    svg += f'  <rect x="{x*ps}" y="{y*ps}" width="{ps}" height="{ps}" fill="#{r:02x}{g:02x}{b:02x}" stroke="#eeeeee" stroke-width="0.5"/>\n'
            svg += '</svg>'
            with open(path, 'w', encoding='utf-8') as f:
                f.write(svg)
            self.update_status(f"✅ SVG 已导出：{os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("导出 SVG 错误", str(e))

    def save_image(self):
        if self.result_image is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
            filetypes=[("PNG图片","*.png"),("JPEG图片","*.jpg"),("BMP图片","*.bmp")])
        if path:
            try:
                self.result_image.save(path)
                self.update_status(f"已保存：{os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("保存错误", str(e))

    def save_image_as(self):
        if self.result_image is None:
            messagebox.showwarning("提示", "没有可保存的像素画")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
            filetypes=[("PNG图片","*.png"),("JPEG图片","*.jpg"),("BMP图片","*.bmp")])
        if path:
            try:
                self.result_image.save(path)
                self.update_status(f"已保存：{os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("保存错误", str(e))

    def save_all(self):
        if self.original_image is None:
            messagebox.showwarning("提示", "没有图片可保存")
            return
        if not self.is_batch_mode:
            if self.batch_images:
                current_path = self.batch_images[self.batch_index]
                folder = os.path.dirname(current_path)
                output_folder = os.path.join(folder, "pixel_output")
                os.makedirs(output_folder, exist_ok=True)
                base = os.path.splitext(os.path.basename(current_path))[0]
                save_path = os.path.join(output_folder, f"{base}_pixel.png")
                try:
                    if self.result_image:
                        self.result_image.save(save_path)
                        self.update_status(f"已保存到：{os.path.basename(save_path)}")
                except Exception as e:
                    messagebox.showerror("保存错误", str(e))
            else:
                self.save_image_as()
            return
        if not self.batch_images:
            messagebox.showinfo("提示", "没有批量图片")
            return
        folder = os.path.dirname(self.batch_images[0])
        output_folder = os.path.join(folder, "pixel_output")
        os.makedirs(output_folder, exist_ok=True)
        total = len(self.batch_images)
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i, img_path in enumerate(self.batch_images):
                futures.append(executor.submit(self._save_one_image, img_path))
            for f in futures:
                f.result()
        self.update_status(f"全部保存完成！共 {total} 张图片")
        messagebox.showinfo("完成", f"全部保存完成！\n共保存 {total} 张图片\n位置：{output_folder}")

    def _save_one_image(self, img_path):
        try:
            img = Image.open(img_path).convert("RGBA")
            block, colors = self.block_var.get(), self.color_var.get()
            palette = PALETTES.get(self.palette_var.get())
            result = self.process_image(img, block, colors, palette, save_editor=False)
            if result:
                folder = os.path.dirname(img_path)
                output_folder = os.path.join(folder, "pixel_output")
                os.makedirs(output_folder, exist_ok=True)
                base = os.path.splitext(os.path.basename(img_path))[0]
                save_path = os.path.join(output_folder, f"{base}_pixel.png")
                result.save(save_path)
        except Exception as e:
            print(f"处理 {img_path} 失败：{e}")

    def open_editor(self):
        if self.result_image is None:
            messagebox.showwarning("提示", "请先生成像素画")
            return
        if self.edit_window is not None and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return
        self.edit_window = tk.Toplevel(self.root)
        self.edit_window.title("✏️ 像素画编辑器")
        self.edit_window.geometry("750x650")
        self.edit_window.minsize(550, 450)

        self.undo_stack, self.redo_stack = [], []
        self.edit_tool = "brush"
        self.current_color = (255, 0, 0)
        self.edit_selection = []
        self.edit_selection_start = None
        self.selection_rect_id = None
        self.edit_clipboard = []

        grid_data = self.grid_colors
        self.edit_grid_w, self.edit_grid_h = len(grid_data[0]) if grid_data else 0, len(grid_data)
        self.edit_grid = [row[:] for row in grid_data]

        top = tk.Frame(self.edit_window); top.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(top, text="工具:").pack(side=tk.LEFT)
        tools = tk.Frame(top); tools.pack(side=tk.LEFT, padx=5)
        self.tool_var = tk.StringVar(value="画笔")
        for t, label in [("画笔","🖊️ 画笔"), ("橡皮","🧹 橡皮"), ("框选","🔲 框选"), ("填充","🪣 填充"), ("吸管","💉 吸管")]:
            tk.Radiobutton(tools, text=label, variable=self.tool_var, value=t, command=self.set_tool).pack(side=tk.LEFT, padx=2)
        tk.Label(top, text="  ").pack(side=tk.LEFT)
        self.color_preview = tk.Canvas(top, width=30, height=30, bg="#FF0000", highlightthickness=2)
        self.color_preview.pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="选择颜色", command=self.choose_color).pack(side=tk.LEFT, padx=5)
        tk.Label(top, text="  ").pack(side=tk.LEFT)
        tk.Button(top, text="↩ 撤销", command=self.editor_undo).pack(side=tk.LEFT, padx=2)
        tk.Button(top, text="↪ 重做", command=self.editor_redo).pack(side=tk.LEFT, padx=2)
        tk.Button(top, text="📋 复制", command=self.editor_copy).pack(side=tk.LEFT, padx=2)
        tk.Button(top, text="📄 粘贴", command=self.editor_paste).pack(side=tk.LEFT, padx=2)
        tk.Button(top, text="🗑️ 清空选择", command=self.editor_clear_selection).pack(side=tk.LEFT, padx=2)
        tk.Button(top, text="✅ 保存并关闭", command=self.save_editor).pack(side=tk.RIGHT, padx=5)

        hint_frame = tk.Frame(self.edit_window); hint_frame.pack(fill=tk.X, padx=10, pady=(0,5))
        self.hint_label = tk.Label(hint_frame, text="💡 画笔：点击修改 | 框选：拖拽选多个 | 填充：点击区域自动填色 | 吸管：拾取颜色", fg="#888", font=("Arial",9))
        self.hint_label.pack()

        canvas_frame = tk.Frame(self.edit_window); canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.edit_canvas = tk.Canvas(canvas_frame, bg="#1e1e1e", highlightthickness=0)
        self.edit_canvas.pack(fill=tk.BOTH, expand=True)
        self.edit_canvas.bind("<Configure>", self.draw_edit_grid)
        self.edit_canvas.bind("<Button-1>", self.on_edit_click)
        self.edit_canvas.bind("<B1-Motion>", self.on_edit_drag)
        self.edit_canvas.bind("<ButtonRelease-1>", self.on_edit_release)
        self.edit_canvas.bind("<KeyPress>", self.on_edit_key)
        self.edit_canvas.focus_set()
        self.draw_edit_grid()

    def set_tool(self):
        self.edit_tool = self.tool_var.get()
        if self.edit_tool != "框选":
            self.clear_selection()
        self.update_hint()

    def update_hint(self):
        hints = {
            "画笔": "🖊️ 点击像素块修改颜色",
            "橡皮": "🧹 点击像素块擦除",
            "框选": "🔲 拖拽选中，方向键移动",
            "填充": "🪣 点击区域自动填充",
            "吸管": "💉 拾取像素颜色"
        }
        self.hint_label.config(text=f"💡 {hints.get(self.edit_tool, '')}")

    def choose_color(self):
        color = colorchooser.askcolor(title="选择颜色", initialcolor=self.current_color)
        if color and color[0]:
            self.current_color = tuple(int(c) for c in color[0])
            self.color_preview.config(bg=f"#{self.current_color[0]:02x}{self.current_color[1]:02x}{self.current_color[2]:02x}")

    def draw_edit_grid(self, event=None):
        if self.edit_grid_w == 0 or self.edit_grid_h == 0:
            return
        cw, ch = self.edit_canvas.winfo_width(), self.edit_canvas.winfo_height()
        if cw < 10 or ch < 10:
            return
        cell = min(cw / self.edit_grid_w, ch / self.edit_grid_h)
        ox, oy = (cw - cell * self.edit_grid_w) / 2, (ch - cell * self.edit_grid_h) / 2
        self.edit_cell_size, self.edit_offset_x, self.edit_offset_y = cell, ox, oy
        self.edit_canvas.delete("all")
        for y in range(self.edit_grid_h):
            for x in range(self.edit_grid_w):
                col = self.edit_grid[y][x]
                x0, y0 = ox + x * cell, oy + y * cell
                self.edit_canvas.create_rectangle(x0, y0, x0 + cell, y0 + cell,
                                                   fill=f"#{col[0]:02x}{col[1]:02x}{col[2]:02x}",
                                                   outline="#333", width=1, tags=f"cell_{y}_{x}")
        for sx, sy in self.edit_selection:
            x0, y0 = ox + sx * cell, oy + sy * cell
            self.edit_canvas.create_rectangle(x0, y0, x0 + cell, y0 + cell,
                                               outline="#00FF00", width=3, tags="selection")

    def get_grid_pos(self, x, y):
        rx, ry = x - self.edit_offset_x, y - self.edit_offset_y
        if rx < 0 or ry < 0:
            return None
        gx, gy = int(rx / self.edit_cell_size), int(ry / self.edit_cell_size)
        if gx >= self.edit_grid_w or gy >= self.edit_grid_h:
            return None
        return (gx, gy)

    def on_edit_click(self, event):
        self.edit_canvas.focus_set()
        pos = self.get_grid_pos(event.x, event.y)
        if not pos:
            return
        gx, gy = pos
        if self.edit_tool == "填充":
            self.flood_fill(gx, gy)
            return
        if self.edit_tool == "吸管":
            col = self.edit_grid[gy][gx]
            self.current_color = col
            self.color_preview.config(bg=f"#{col[0]:02x}{col[1]:02x}{col[2]:02x}")
            self.update_hint()
            return
        if self.edit_tool == "框选":
            self.edit_selection_start = pos
            self.clear_selection()
            return
        self.edit_pixel_at(gx, gy)

    def on_edit_drag(self, event):
        pos = self.get_grid_pos(event.x, event.y)
        if not pos:
            return
        if self.edit_tool == "框选" and self.edit_selection_start:
            sx, sy = self.edit_selection_start
            cx, cy = pos
            if self.selection_rect_id:
                self.edit_canvas.delete(self.selection_rect_id)
            x0 = self.edit_offset_x + min(sx, cx) * self.edit_cell_size
            y0 = self.edit_offset_y + min(sy, cy) * self.edit_cell_size
            x1 = self.edit_offset_x + (max(sx, cx) + 1) * self.edit_cell_size
            y1 = self.edit_offset_y + (max(sy, cy) + 1) * self.edit_cell_size
            self.selection_rect_id = self.edit_canvas.create_rectangle(x0, y0, x1, y1,
                                                                       outline="#00FF00", width=2, dash=(4,4))
            return
        if self.edit_tool in ["画笔", "橡皮"]:
            self.edit_pixel_at(pos[0], pos[1])

    def on_edit_release(self, event):
        if self.edit_tool == "框选" and self.edit_selection_start:
            pos = self.get_grid_pos(event.x, event.y)
            if pos:
                sx, sy = self.edit_selection_start
                cx, cy = pos
                self.edit_selection = [(x, y) for y in range(min(sy, cy), max(sy, cy)+1)
                                        for x in range(min(sx, cx), max(sx, cx)+1)
                                        if 0 <= x < self.edit_grid_w and 0 <= y < self.edit_grid_h]
                self.update_hint()
            self.edit_selection_start = None
            self.draw_edit_grid()

    def flood_fill(self, sx, sy):
        target = self.edit_grid[sy][sx]
        fill = self.current_color
        if target == fill:
            return
        self.undo_stack.append(("flood_fill", sx, sy, target, fill))
        q = deque([(sx, sy)])
        visited = {(sx, sy)}
        while q:
            x, y = q.popleft()
            if not (0 <= x < self.edit_grid_w and 0 <= y < self.edit_grid_h):
                continue
            if self.edit_grid[y][x] != target:
                continue
            self.edit_grid[y][x] = fill
            for dx, dy in ((1,0), (-1,0), (0,1), (0,-1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.edit_grid_w and 0 <= ny < self.edit_grid_h:
                    if (nx, ny) not in visited and self.edit_grid[ny][nx] == target:
                        visited.add((nx, ny))
                        q.append((nx, ny))
        self.draw_edit_grid()

    def editor_copy(self):
        if not self.edit_selection:
            messagebox.showinfo("提示", "请先用框选工具选中像素区域")
            return
        self.edit_clipboard = [(x, y, self.edit_grid[y][x]) for (x, y) in self.edit_selection]
        self.update_hint()

    def editor_paste(self):
        if not self.edit_clipboard:
            messagebox.showinfo("提示", "剪贴板为空，请先复制")
            return
        if not self.edit_selection:
            messagebox.showinfo("提示", "请先选中目标区域左上角的位置（只需选中一个像素）")
            return
        ax, ay = self.edit_selection[0]
        minx = min(x for x, y, c in self.edit_clipboard)
        miny = min(y for x, y, c in self.edit_clipboard)
        for x, y, c in self.edit_clipboard:
            tx, ty = ax + (x - minx), ay + (y - miny)
            if 0 <= tx < self.edit_grid_w and 0 <= ty < self.edit_grid_h:
                if not self.undo_stack or self.undo_stack[-1] != (tx, ty, self.edit_grid[ty][tx]):
                    self.undo_stack.append((tx, ty, self.edit_grid[ty][tx]))
                    self.redo_stack.clear()
                self.edit_grid[ty][tx] = c
        self.draw_edit_grid()

    def editor_clear_selection(self):
        if not self.edit_selection:
            return
        for x, y in self.edit_selection:
            if not self.undo_stack or self.undo_stack[-1] != (x, y, self.edit_grid[y][x]):
                self.undo_stack.append((x, y, self.edit_grid[y][x]))
                self.redo_stack.clear()
            self.edit_grid[y][x] = (128, 128, 128)
        self.edit_selection.clear()
        self.draw_edit_grid()

    def clear_selection(self):
        self.edit_selection.clear()
        self.edit_selection_start = None
        if self.selection_rect_id:
            self.edit_canvas.delete(self.selection_rect_id)
            self.selection_rect_id = None
        self.update_hint()

    def on_edit_key(self, event):
        if not self.edit_selection:
            return
        dx = dy = 0
        if event.keysym == "Left":
            dx = -1
        elif event.keysym == "Right":
            dx = 1
        elif event.keysym == "Up":
            dy = -1
        elif event.keysym == "Down":
            dy = 1
        else:
            return
        new_sel = []
        for x, y in self.edit_selection:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.edit_grid_w and 0 <= ny < self.edit_grid_h:
                new_sel.append((nx, ny))
            else:
                return
        for x, y in self.edit_selection:
            if not self.undo_stack or self.undo_stack[-1] != (x, y, self.edit_grid[y][x]):
                self.undo_stack.append((x, y, self.edit_grid[y][x]))
                self.redo_stack.clear()
        old = [row[:] for row in self.edit_grid]
        for x, y in self.edit_selection:
            self.edit_grid[y][x] = (128, 128, 128)
        for i, (x, y) in enumerate(self.edit_selection):
            nx, ny = new_sel[i]
            self.edit_grid[ny][nx] = old[y][x]
        self.edit_selection = new_sel
        self.draw_edit_grid()

    def editor_undo(self):
        if not self.undo_stack:
            return
        item = self.undo_stack.pop()
        if isinstance(item, tuple) and item[0] == "flood_fill":
            _, sx, sy, target, fill = item
            q = deque([(sx, sy)])
            visited = {(sx, sy)}
            while q:
                x, y = q.popleft()
                if not (0 <= x < self.edit_grid_w and 0 <= y < self.edit_grid_h):
                    continue
                if self.edit_grid[y][x] != fill:
                    continue
                self.edit_grid[y][x] = target
                for dx, dy in ((1,0), (-1,0), (0,1), (0,-1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.edit_grid_w and 0 <= ny < self.edit_grid_h:
                        if (nx, ny) not in visited and self.edit_grid[ny][nx] == fill:
                            visited.add((nx, ny))
                            q.append((nx, ny))
        else:
            gx, gy, old_color = item
            self.redo_stack.append((gx, gy, self.edit_grid[gy][gx]))
            self.edit_grid[gy][gx] = old_color
        self.draw_edit_grid()

    def editor_redo(self):
        if not self.redo_stack:
            return
        gx, gy, new_color = self.redo_stack.pop()
        self.undo_stack.append((gx, gy, self.edit_grid[gy][gx]))
        self.edit_grid[gy][gx] = new_color
        self.draw_edit_grid()

    def edit_pixel_at(self, gx, gy):
        if not (0 <= gx < self.edit_grid_w and 0 <= gy < self.edit_grid_h):
            return
        if not self.undo_stack or self.undo_stack[-1] != (gx, gy, self.edit_grid[gy][gx]):
            self.undo_stack.append((gx, gy, self.edit_grid[gy][gx]))
            self.redo_stack.clear()
        color = (128, 128, 128) if self.edit_tool == "橡皮" else self.current_color
        self.edit_grid[gy][gx] = color
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
            self._cached_res_display = None
            self.show_image(new_result, "res")
            self.update_status("编辑已应用")
        self.edit_window.destroy()
        self.edit_window = None

    def show_help(self):
        messagebox.showinfo(
            "使用说明",
            "PixelCraft 使用说明\n\n"
            "1. 点击「选择图片」或拖拽图片到窗口\n"
            "2. 调整「块大小」控制像素颗粒感\n"
            "3. 调整「颜色数」或选择「色盘」控制色彩\n"
            "4. 点击「编辑像素画」进入编辑器\n"
            "   🖊️ 画笔：点击修改颜色\n"
            "   🧹 橡皮：擦除像素\n"
            "   🔲 框选：拖拽选中多个像素\n"
            "   🪣 填充：点击区域自动填充颜色\n"
            "   💉 吸管：拾取像素颜色\n"
            "5. 点击「对比视图」左右对比原图和像素画\n"
            "6. 点击「保存像素画」导出为 PNG/JPG/BMP\n"
            "7. 点击「导出 SVG」生成矢量图\n\n"
            "💡 鼠标滚轮可缩放图片，双击恢复"
        )

    def show_about(self):
        messagebox.showinfo(
            "关于 PixelCraft",
            "PixelCraft\n\n将任意图片转换为像素画的桌面工具。\n\n"
            "作者: Grass114\n许可: MIT License\nGitHub: https://github.com/Grass114/PixelCraft"
        )

    def load_config(self):
        base_dir = get_base_dir()
        path = os.path.join(base_dir, "pixelcraft_config.json")
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    cfg = json.load(f)
                self.block_var.set(cfg.get("block_size", 12))
                self.color_var.set(cfg.get("colors", 16))
                self.block_label.config(text=str(self.block_var.get()))
                self.color_label.config(text=str(self.color_var.get()))
            except Exception as e:
                print(f"加载配置文件失败: {e}")

    def save_config(self):
        try:
            base_dir = get_base_dir()
            path = os.path.join(base_dir, "pixelcraft_config.json")
            with open(path, 'w') as f:
                json.dump({
                    "block_size": self.block_var.get(),
                    "colors": self.color_var.get()
                }, f)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def update_status(self, msg):
        self.status.config(text=msg)


if __name__ == "__main__":
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = PixelCraft(root)
    root.mainloop()
