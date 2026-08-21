import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import math

# ---------- 复古调色板 ----------
PALETTES = {
    "自动": None,  # 表示使用算法量化
    "GameBoy (4色)": [
        (15, 56, 15),   # 深绿
        (48, 98, 48),   # 中绿
        (139, 172, 15), # 亮绿
        (155, 188, 15), # 黄绿
    ],
    "NES (经典54色)": [  # 取部分代表性颜色
        (0, 0, 0), (255, 255, 255), (252, 0, 0), (0, 252, 0),
        (0, 0, 252), (252, 252, 0), (252, 0, 252), (0, 252, 252),
        (252, 128, 0), (0, 128, 0), (0, 0, 128), (128, 0, 128),
        (128, 128, 0), (0, 128, 128), (128, 128, 128), (192, 192, 192),
        (252, 128, 128), (128, 252, 128), (128, 128, 252), (252, 252, 128),
    ],
    "CGA 4色": [
        (0, 0, 0),       # 黑
        (255, 255, 255), # 白
        (0, 255, 255),   # 青
        (255, 0, 255),   # 紫
    ],
    "CGA 16色": [  # 扩展16色
        (0,0,0), (0,0,170), (0,170,0), (0,170,170),
        (170,0,0), (170,0,170), (170,85,0), (170,170,170),
        (85,85,85), (85,85,255), (85,255,85), (85,255,255),
        (255,85,85), (255,85,255), (255,255,85), (255,255,255),
    ]
}

def apply_palette(image, palette_colors):
    """将 RGB 图片的每个像素替换为调色板中最接近的颜色"""
    if palette_colors is None:
        return image  # 自动模式，不处理
    # 将图片转为列表处理，加快速度
    pixels = image.load()
    w, h = image.size
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            best = None
            min_dist = float('inf')
            for pr, pg, pb in palette_colors:
                dist = (r-pr)**2 + (g-pg)**2 + (b-pb)**2
                if dist < min_dist:
                    min_dist = dist
                    best = (pr, pg, pb)
            pixels[x, y] = best
    return image

# ---------- 主类 ----------
class PixelArtPro:
    def __init__(self, root):
        self.root = root
        root.title("🎨 像素画生成器 Pro")
        root.geometry("700x550")
        root.minsize(600, 450)

        # 存储
        self.original_image = None
        self.result_image = None
        self.orig_tk = None
        self.res_tk = None
        self.current_display_size = (0, 0)
        self.after_id = None  # 防抖定时器

        # 启用拖放（需 tkinterdnd2）
        self.setup_drag_drop()

        # ---------- 顶部：文件选择 ----------
        top = tk.Frame(root)
        top.pack(pady=8, padx=10, fill=tk.X)

        tk.Button(top, text="📂 选择图片", command=self.load_image, width=10).pack(side=tk.LEFT, padx=(0,5))
        self.file_label = tk.Label(top, text="未选择文件", anchor="w", relief="sunken")
        self.file_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # ---------- 参数行 ----------
        param = tk.Frame(root)
        param.pack(pady=5, padx=10, fill=tk.X)

        # 块大小
        tk.Label(param, text="块:").pack(side=tk.LEFT, padx=(0,2))
        self.block_var = tk.IntVar(value=12)
        self.block_scale = tk.Scale(param, from_=2, to=30, orient=tk.HORIZONTAL,
                                    variable=self.block_var, length=100, showvalue=0)
        self.block_scale.pack(side=tk.LEFT, padx=(0,5))
        self.block_label = tk.Label(param, text="12", width=3)
        self.block_label.pack(side=tk.LEFT, padx=(0,10))
        self.block_scale.config(command=lambda v: (self.block_label.config(text=v), self.schedule_convert()))

        # 颜色预设
        tk.Label(param, text="色盘:").pack(side=tk.LEFT, padx=(0,2))
        self.palette_var = tk.StringVar(value="自动")
        self.palette_combo = ttk.Combobox(param, textvariable=self.palette_var,
                                          values=list(PALETTES.keys()), state="readonly", width=14)
        self.palette_combo.pack(side=tk.LEFT, padx=(0,10))
        self.palette_combo.bind("<<ComboboxSelected>>", lambda e: self.schedule_convert())

        # 颜色数（仅自动模式有效）
        tk.Label(param, text="颜色数:").pack(side=tk.LEFT, padx=(0,2))
        self.colors_var = tk.IntVar(value=16)
        self.colors_scale = tk.Scale(param, from_=2, to=64, orient=tk.HORIZONTAL,
                                     variable=self.colors_var, length=100, showvalue=0)
        self.colors_scale.pack(side=tk.LEFT, padx=(0,5))
        self.colors_label = tk.Label(param, text="16", width=3)
        self.colors_label.pack(side=tk.LEFT, padx=(0,5))
        self.colors_scale.config(command=lambda v: (self.colors_label.config(text=v), self.schedule_convert()))

        # ---------- 图片显示 ----------
        display = tk.Frame(root)
        display.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        left = tk.LabelFrame(display, text="原图", font=("Arial", 9))
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5))
        self.orig_canvas = tk.Canvas(left, bg="#f0f0f0", highlightthickness=0)
        self.orig_canvas.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        right = tk.LabelFrame(display, text="像素画", font=("Arial", 9))
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5,0))
        self.res_canvas = tk.Canvas(right, bg="#f0f0f0", highlightthickness=0)
        self.res_canvas.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # ---------- 底部 ----------
        bottom = tk.Frame(root)
        bottom.pack(pady=8, padx=10, fill=tk.X)

        self.save_btn = tk.Button(bottom, text="💾 保存像素画", command=self.save_image,
                                  state=tk.DISABLED, bg="#2196F3", fg="white")
        self.save_btn.pack(side=tk.LEFT, padx=(0,15))

        self.status = tk.Label(bottom, text="拖拽图片或点击选择", fg="blue", anchor="w")
        self.status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 绑定窗口缩放
        self.root.bind("<Configure>", self.on_resize)

    # ---------- 拖放支持 ----------
    def setup_drag_drop(self):
        try:
            from tkinterdnd2 import TkinterDnD
            # 如果 root 已经是 TkinterDnD 类型，直接使用
            if not isinstance(self.root, TkinterDnD.Tk):
                # 重新创建 root
                self.root.destroy()
                self.root = TkinterDnD.Tk()
                # 需要重新设置所有控件，这里简单提示
                messagebox.showwarning("拖放支持", "请安装 tkinterdnd2 并重启程序")
            else:
                self.root.drop_target_register('DND_Files')
                self.root.dnd_bind('<<Drop>>', self.on_drop)
        except ImportError:
            # 如果没有 tkinterdnd2，拖放功能不可用，但不会报错
            pass
        except Exception:
            pass

    def on_drop(self, event):
        # 获取拖放的文件路径（可能有多个，取第一个）
        files = event.data.split()
        if files:
            path = files[0].strip('{}')  # 去除可能的花括号
            if os.path.isfile(path):
                self.load_image_from_path(path)

    def load_image_from_path(self, path):
        try:
            self.original_image = Image.open(path).convert("RGB")
            self.file_label.config(text=os.path.basename(path))
            self.result_image = None
            self.res_canvas.delete("all")
            self.save_btn.config(state=tk.DISABLED)
            self.current_display_size = (0, 0)
            self.after_idle_refresh()
            self.status.config(text="已加载，自动转换中...")
            self.schedule_convert(immediate=True)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片：{e}")

    # ---------- 图片加载 ----------
    def load_image(self):
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif"), ("所有文件", "*.*")]
        )
        if path:
            self.load_image_from_path(path)

    # ---------- 防抖转换 ----------
    def schedule_convert(self, immediate=False):
        if self.original_image is None:
            return
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if immediate:
            self.do_convert()
        else:
            self.after_id = self.root.after(200, self.do_convert)  # 200ms 防抖

    # ---------- 转换核心 ----------
    def do_convert(self):
        if self.original_image is None:
            return
        block = self.block_var.get()
        colors = self.colors_var.get()
        palette_name = self.palette_var.get()
        palette = PALETTES.get(palette_name)

        try:
            img = self.original_image.copy()
            w, h = img.size
            sw = max(1, w // block)
            sh = max(1, h // block)
            small = img.resize((sw, sh), Image.NEAREST)

            # 应用色盘（如果非自动）
            if palette is not None:
                small = apply_palette(small, palette)
            else:
                # 自动量化
                if colors < 256:
                    small = small.quantize(colors=colors, method=Image.MEDIANCUT)
                    small = small.convert("RGB")

            self.result_image = small.resize((w, h), Image.NEAREST)
            self.show_image(self.result_image, self.res_canvas)
            self.save_btn.config(state=tk.NORMAL)

            # 更新状态：网格尺寸
            grid_w = sw
            grid_h = sh
            self.status.config(text=f"网格：{grid_w}×{grid_h}  |  块大小 {block}  |  色盘：{palette_name}")
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
            self.orig_tk = tk_img
        else:
            self.res_tk = tk_img

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

    # ---------- 保存 ----------
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
                self.status.config(text=f"已保存：{os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("保存错误", str(e))

if __name__ == "__main__":
    # 尝试使用 TkinterDnD 作为根窗口
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except ImportError:
        root = tk.Tk()
        print("提示：未安装 tkinterdnd2，拖放功能不可用。安装：pip install tkinterdnd2")
    app = PixelArtPro(root)
    root.mainloop()