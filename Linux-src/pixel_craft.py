import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import json
import sys
import subprocess
import random
import threading
import time
from collections import deque

try:
    from tkinterdnd2 import TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("提示：未安装 tkinterdnd2，拖拽功能不可用。安装：pip install tkinterdnd2")

try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
    RESAMPLE_NEAREST = Image.Resampling.NEAREST
    RESAMPLE_BILINEAR = Image.Resampling.BILINEAR
    RESAMPLE_BICUBIC = Image.Resampling.BICUBIC
except AttributeError:
    RESAMPLE_LANCZOS = Image.LANCZOS
    RESAMPLE_NEAREST = Image.NEAREST
    RESAMPLE_BILINEAR = Image.BILINEAR
    RESAMPLE_BICUBIC = Image.BICUBIC

try:
    DITHER_NONE = Image.Dither.NONE
    DITHER_FS = Image.Dither.FLOYDSTEINBERG
except AttributeError:
    DITHER_NONE = Image.NONE
    DITHER_FS = Image.FLOYDSTEINBERG


VERSION = "v1.7"

LOG_DEBUG = 10
LOG_INFO = 20
LOG_WARNING = 30
LOG_ERROR = 40
LOG_NONE = 100

LOG_LEVEL_NAMES = {
    "DEBUG": LOG_DEBUG,
    "INFO": LOG_INFO,
    "WARNING": LOG_WARNING,
    "ERROR": LOG_ERROR,
    "NONE": LOG_NONE,
}
LOG_LEVEL_NUMS = {v: k for k, v in LOG_LEVEL_NAMES.items()}

KAOMOJI_LIST = [
    "(＾▽＾)", "(￣▽￣)", "(｡•́︿•̀｡)", "(๑•̀ㅂ•́)و", "(＾ω＾)",
    "(´・ω・`)", "(￣ω￣)", "(≧▽≦)", "(￣ε￣)", "(｡･ω･｡)",
    "(ノ°▽°)ノ", "(・∀・)", "(￣▽￣)ノ", "(｡◕‿◕｡)", "(＾▽＾)/",
    "(・ω・)", "(´▽`)", "(≧∇≦)/", "(￣ー￣)", "(＾_＾)",
    "(^_^)", "(¬_¬)", "(￣▽￣;)", "(・_・;)", "(°ー°)",
    "(￣□￣)", "(＠_＠)", "(￣～￣)", "(￣ω￣;)", "(・へ・)",
    "(๑¯ω¯๑)", "(｡>﹏<｡)", "(＾▽＾)b", "(￣▽￣)ゞ", "(・∀・)ノ",
    "(◕‿◕)", "(◕ᴗ◕)", "(≧ω≦)", "(￣▽￣)~", "(ノ￣▽￣)ノ",
    "(￣▽￣)/", "(・ω・)ノ", "(´・ω・)ノ", "(￣ヘ￣)", "(￣^￣)",
    "(￣0￣)", "(・o・)", "(°o°)", "(￣□￣;)", "(＾ω＾)b",
    "(｡･ω･｡)ﾉ", "(｡>ㅅ<｡)", "(๑>ᴗ<๑)", "(・∀・)b", "(＾▽＾)ゞ",
    "(￣▽￣)b", "(´ω`)", "(°ω°)", "(・_・)", "(￣▽￣)",
    "(＾ω＾)", "(｡◕‿◕｡)", "(◕‿◕)",
]

DEV_DEFAULTS = {
    "version_text": VERSION,
    "kaomoji_csv": ",".join(KAOMOJI_LIST),
    "presets_json": '{"16×16":[16,16],"32×32":[32,32],"48×48":[48,48],"64×64":[64,64],"128×128":[128,128]}',
    "recent_max": 5,
    "palette_cache_enabled": True,
    "log_file_path": "pixelcraft.log",
    "log_max_lines": 5000,

    "block_min": 2,
    "block_max": 40,
    "colors_min": 2,
    "colors_max": 64,
    "preset_new_block_cap": 40,
    "min_window_width": 800,
    "min_window_height": 600,
    "recent_menu_truncate": 40,

    "convert_debounce_ms": 150,
    "batch_threads": 4,
    "batch_poll_ms": 200,
    "smooth_resize_threshold": 2000,

    "bayer_spread_multiplier": 1.0,
    "atkinson_error_scale": 1.0,
    "nearest_use_weighted": False,
    "nearest_weight_r": 2.0,
    "nearest_weight_g": 4.0,
    "nearest_weight_b": 3.0,
    "exif_transpose": True,

    "jpg_quality": 95,
    "png_compress_level": 6,
    "png_optimize": False,

    "zoom_in_factor": 1.15,
    "zoom_out_factor": 0.85,
    "zoom_min": 0.1,
    "zoom_max": 10.0,

    "canvas_bg": "#1e1e1e",
    "editor_canvas_bg": "#1e1e1e",
    "status_fg": "blue",
    "status_success_fg": "green",
    "status_error_fg": "red",
    "editor_selection_color": "#00FF00",
    "editor_drag_color": "#00FF00",
    "font_family": "",
    "font_size": 0,

    "log_level": "INFO",
    "log_to_console": False,
    "log_to_file": False,

    "show_convert_time": True,
    "debug_console": False,
    "editor_grid_render_threshold": 0,
    "show_hover_coords": True,

    "continuous_drag_draw": True,
    "editor_mousewheel_zoom": False,

    "watch_refresh_ms": 250,
}

DITHER_DISPLAY = {
    "NONE": "无",
    "FLOYDSTEINBERG": "Floyd-Steinberg",
    "BAYER4": "Bayer 4×4",
    "BAYER8": "Bayer 8×8",
    "ATKINSON": "Atkinson",
}
DITHER_DISPLAY_INV = {v: k for k, v in DITHER_DISPLAY.items()}

BAYER_4 = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]

BAYER_8 = [
    [0, 48, 12, 60, 3, 51, 15, 63],
    [32, 16, 44, 28, 35, 19, 47, 31],
    [8, 56, 4, 52, 11, 59, 7, 55],
    [40, 24, 36, 20, 43, 27, 39, 23],
    [2, 50, 14, 62, 1, 49, 13, 61],
    [34, 18, 46, 30, 33, 17, 45, 29],
    [10, 58, 6, 54, 9, 57, 5, 53],
    [42, 26, 38, 22, 41, 25, 37, 21],
]

DEFAULT_SETTINGS = {
    "show_kaomoji": True,
    "title_custom_suffix": "",
    "window_width": 885,
    "window_height": 636,
    "wheel_zoom_step": 0.1,
    "default_block": 12,
    "default_colors": 16,
    "default_palette": "自动",
    "remember_last_params": True,
    "quantize_method": "MEDIANCUT",
    "dither_method": "NONE",
    "undo_limit": 100,
    "brush_size": 1,
    "eraser_color": [128, 128, 128],
    "default_show_grid": True,
    "grid_line_color": "#333333",
    "default_tool": "画笔",
    "default_save_format": "PNG",
    "fixed_save_dir": "",
    "resample_original": "BILINEAR",
    "resample_result": "NEAREST",
}


def get_base_dir():
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

MAX_RECENT = 5

_palette_cache = {}


class PixelCraft:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()

        self.settings = dict(DEFAULT_SETTINGS)
        self.dev = dict(DEV_DEFAULTS)
        self.recent_files = []
        self._config_last_block = None
        self._config_last_colors = None
        self._config_last_palette = None
        self._load_config_file()
        self._init_dev_dependent()

        self._update_title()
        self.root.geometry(f"{self.settings['window_width']}x{self.settings['window_height']}")
        self.root.minsize(int(self.dev.get("min_window_width", 800)),
                          int(self.dev.get("min_window_height", 600)))

        ff = self.dev.get("font_family", "") or ""
        fs = int(self.dev.get("font_size", 0) or 0)
        if ff or fs > 0:
            f = (ff or "TkDefaultFont", fs if fs > 0 else 10)
            try:
                self.root.option_add("*Font", f)
            except Exception:
                pass

        self.original_image = None
        self.result_image = None
        self.current_display_size = (0, 0)
        self.after_id = None
        self.zoom_factor = 1.0

        self.dirty = False
        self._editor_dirty = False
        self._mark_dirty_on_convert = True

        self._converting = False
        self._pending_convert = False
        self._closing = False

        self.batch_images = []
        self.batch_index = 0
        self.is_batch_mode = False

        self.compare_window = None
        self._pref_window = None
        self._watch_window = None
        self._watch_text = None

        self.edit_window = None
        self.grid_colors = []
        self.grid_w = 0
        self.grid_h = 0
        self.undo_stack = deque(maxlen=int(self.settings["undo_limit"]))
        self.redo_stack = deque(maxlen=int(self.settings["undo_limit"]))
        self.current_color = (255, 0, 0)
        self.edit_tool = "brush"
        self.show_grid_lines = True

        self.edit_selection = []
        self.edit_selection_start = None
        self.selection_rect_id = None
        self.edit_clipboard = []
        self.cell_items = []
        self._stroke_active = False
        self.edit_cell_size = 1
        self.edit_offset_x = 0
        self.edit_offset_y = 0

        self.pan_data = None
        self.main_frame = None

        self._cached_orig_display = None
        self._cached_res_display = None

        self._mouse_main_canvas = None
        self._mouse_editor_grid = None

        if HAS_DND and isinstance(root, TkinterDnD.Tk):
            root.drop_target_register('DND_Files')
            root.dnd_bind('<<Drop>>', self.on_drop)

        self.setup_ui()
        self._apply_config_to_ui()
        self._rebuild_recent_menu()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind_all("<F12>", self.toggle_watch)
        self.root.deiconify()
        self.update_status("拖拽图片或点击「选择图片」开始")
        self.root.after_idle(self._post_startup)

    def _post_startup(self):
        self._dev_log(f"启动完成，版本 {self.dev.get('version_text', VERSION)}", LOG_INFO)

    # ============================ 延迟导入 ============================
    def _pick_color(self, **kwargs):
        from tkinter import colorchooser
        return colorchooser.askcolor(**kwargs)

    def _get_palette_image(self, colors):
        if not colors:
            return None
        use_cache = bool(self.dev.get("palette_cache_enabled", True))
        if use_cache:
            key = tuple(colors)
            if key in _palette_cache:
                return _palette_cache[key]
        palette_img = Image.new('P', (1, len(colors)))
        palette_img.putdata(list(range(len(colors))))
        palette = []
        for c in colors:
            palette.extend(c)
        palette_img.putpalette(palette)
        if use_cache:
            _palette_cache[tuple(colors)] = palette_img
        return palette_img

    def _init_dev_dependent(self):
        kaomoji_list = [s.strip() for s in self.dev.get("kaomoji_csv", "").split(",") if s.strip()]
        if not kaomoji_list:
            kaomoji_list = list(KAOMOJI_LIST)
        self._kaomoji_list = kaomoji_list
        self.kaomoji = random.choice(kaomoji_list) if kaomoji_list else "(・_・)"

        try:
            presets = json.loads(self.dev.get("presets_json", "{}"))
            if not isinstance(presets, dict) or not presets:
                raise ValueError
            self.presets = {str(k): tuple(int(x) for x in v) for k, v in presets.items()}
        except Exception:
            self.presets = dict(PRESETS)

        self._log_level_num = LOG_LEVEL_NAMES.get(self.dev.get("log_level", "INFO"), LOG_INFO)
        self._preset_new_block_cap = max(1, int(self.dev.get("preset_new_block_cap", 40)))

    # ============================ 日志 ============================
    def _dev_log(self, msg, level=None):
        if level is None:
            level = LOG_DEBUG
        try:
            threshold = getattr(self, "_log_level_num", LOG_INFO)
        except Exception:
            threshold = LOG_INFO
        if level < threshold:
            return
        ts = time.strftime("%H:%M:%S")
        lv_name = LOG_LEVEL_NUMS.get(level, "DEBUG")
        line = f"[{ts}] [{lv_name}] {msg}"
        if self.dev.get("debug_console", False) or self.dev.get("log_to_console", False):
            try:
                print("[PixelCraft]", line)
            except Exception:
                pass
        if self.dev.get("log_to_file", False):
            path = self.dev.get("log_file_path", "pixelcraft.log")
            try:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
                self._trim_log_file(path)
            except Exception:
                pass

    def _trim_log_file(self, path):
        max_lines = max(100, int(self.dev.get("log_max_lines", 5000)))
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) > max_lines:
                with open(path, "w", encoding="utf-8") as f:
                    f.writelines(lines[-max_lines:])
        except Exception:
            pass

    # ============================ 配置 ============================
    def _load_config_file(self):
        path = os.path.join(get_base_dir(), "pixelcraft_config.json")
        if not os.path.exists(path):
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            self.settings.update(cfg.get("settings", {}))
            self.dev.update(cfg.get("dev", {}))
            self.recent_files = [p for p in cfg.get("recent_files", []) if os.path.exists(p)]
            self._config_last_block = cfg.get("block_size")
            self._config_last_colors = cfg.get("colors")
            self._config_last_palette = cfg.get("last_palette")
        except Exception as e:
            print(f"加载配置文件失败: {e}")

    def _apply_config_to_ui(self):
        if self.settings.get("remember_last_params", True):
            block = self._config_last_block if self._config_last_block is not None else self.settings["default_block"]
            colors = self._config_last_colors if self._config_last_colors is not None else self.settings["default_colors"]
            palette = self._config_last_palette if self._config_last_palette is not None else self.settings["default_palette"]
        else:
            block = self.settings["default_block"]
            colors = self.settings["default_colors"]
            palette = self.settings["default_palette"]
        try:
            self.block_var.set(int(block))
            self.color_var.set(int(colors))
        except Exception:
            pass
        if palette in PALETTES:
            self.palette_var.set(palette)
        self.block_label.config(text=str(self.block_var.get()))
        self.color_label.config(text=str(self.color_var.get()))

    def save_config(self):
        try:
            path = os.path.join(get_base_dir(), "pixelcraft_config.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({
                    "settings": self.settings,
                    "dev": self.dev,
                    "block_size": self.block_var.get(),
                    "colors": self.color_var.get(),
                    "last_palette": self.palette_var.get(),
                    "recent_files": self.recent_files,
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def _update_title(self):
        parts = [f"PixelCraft {self.dev.get('version_text', VERSION)}"]
        if self.settings.get("show_kaomoji", True):
            parts.append(self.kaomoji)
        suffix = self.settings.get("title_custom_suffix", "").strip()
        if suffix:
            parts.append(suffix)
        self.root.title(" ".join(parts))

    def _update_editor_title(self):
        if self.edit_window is None or not self.edit_window.winfo_exists():
            return
        if self.settings.get("show_kaomoji", True):
            self.edit_window.title(f"像素画编辑器 {self.kaomoji}")
        else:
            self.edit_window.title("像素画编辑器")

    def _apply_settings(self):
        self._log_level_num = LOG_LEVEL_NAMES.get(self.dev.get("log_level", "INFO"), LOG_INFO)
        self._preset_new_block_cap = max(1, int(self.dev.get("preset_new_block_cap", 40)))
        self._update_title()
        self._update_editor_title()
        self._cached_orig_display = None
        self._cached_res_display = None

        try:
            if hasattr(self, "status"):
                self.status.config(fg=self.dev.get("status_fg", "blue"))
            bg = self.dev.get("canvas_bg", "#1e1e1e")
            for name in ("orig_canvas", "res_canvas"):
                c = getattr(self, name, None)
                if c is not None:
                    try:
                        c.config(bg=bg)
                    except Exception:
                        pass
            if getattr(self, "edit_window", None) is not None and self.edit_window.winfo_exists():
                ec = getattr(self, "edit_canvas", None)
                if ec is not None:
                    try:
                        ec.config(bg=self.dev.get("editor_canvas_bg", "#1e1e1e"))
                    except Exception:
                        pass
        except Exception:
            pass

        if self.original_image:
            self.show_image(self.original_image, "orig")
        if self.result_image:
            self.show_image(self.result_image, "res")
        if self.edit_window is not None and self.edit_window.winfo_exists():
            limit = int(self.settings["undo_limit"])
            if self.undo_stack.maxlen != limit:
                self.undo_stack = deque(self.undo_stack, maxlen=limit)
                self.redo_stack = deque(self.redo_stack, maxlen=limit)
            self.show_grid_lines = bool(self.settings.get("default_show_grid", True))
            if hasattr(self, "grid_lines_var"):
                self.grid_lines_var.set(self.show_grid_lines)
            self.draw_edit_grid()
        self.save_config()

    def on_close(self):
        if self.dirty and self.result_image is not None:
            r = messagebox.askyesnocancel(
                "未保存的修改",
                "当前像素画尚未保存，是否保存后退出？\n\n"
                "「是」保存并退出\n「否」直接退出\n「取消」返回编辑"
            )
            if r is None:
                return
            if r:
                if not self._save_for_exit():
                    return
        self._closing = True
        self.save_config()
        self.root.destroy()

    def _save_for_exit(self):
        if self.result_image is None:
            return True
        path = filedialog.asksaveasfilename(**self._get_save_kwargs())
        if not path:
            return False
        try:
            self._save_image_to(self.result_image, path)
            self.dirty = False
            return True
        except Exception as e:
            messagebox.showerror("保存错误", str(e))
            return False

    def _get_save_kwargs(self):
        fmt = self.settings.get("default_save_format", "PNG")
        ext_map = {"PNG": ".png", "JPG": ".jpg", "BMP": ".bmp"}
        ftype_map = {
            "PNG": [("PNG图片", "*.png")],
            "JPG": [("JPEG图片", "*.jpg")],
            "BMP": [("BMP图片", "*.bmp")],
        }
        kwargs = {
            "defaultextension": ext_map.get(fmt, ".png"),
            "filetypes": ftype_map.get(fmt, [("PNG图片", "*.png")]) + [("所有文件", "*.*")],
        }
        fixed_dir = self.settings.get("fixed_save_dir", "").strip()
        if fixed_dir and os.path.isdir(fixed_dir):
            kwargs["initialdir"] = fixed_dir
        return kwargs

    def _save_image_to(self, img, path):
        ext = os.path.splitext(path)[1].lower()
        target = img
        if ext in (".jpg", ".jpeg") and target.mode == "RGBA":
            target = target.convert("RGB")
        kwargs = {}
        if ext in (".jpg", ".jpeg"):
            kwargs["quality"] = max(1, min(100, int(self.dev.get("jpg_quality", 95))))
        elif ext == ".png":
            kwargs["compress_level"] = max(0, min(9, int(self.dev.get("png_compress_level", 6))))
            if self.dev.get("png_optimize", False):
                kwargs["optimize"] = True
        target.save(path, **kwargs)
        self._dev_log(f"已保存图片：{path}", LOG_INFO)

    def restart_app(self):
        if self.dirty and self.result_image is not None:
            r = messagebox.askyesnocancel(
                "未保存的修改",
                "当前像素画尚未保存，是否保存后重启？\n\n"
                "「是」保存并重启\n「否」直接重启\n「取消」返回"
            )
            if r is None:
                return
            if r and not self._save_for_exit():
                return
        self._closing = True
        self.save_config()
        self.root.quit()
        self.root.destroy()
        if getattr(sys, 'frozen', False):
            subprocess.Popen([sys.executable] + sys.argv)
        else:
            subprocess.Popen([sys.executable, sys.argv[0]])
        sys.exit(0)

    # ============================ 菜单延迟填充 ============================
    def _fill_preset_menu(self, menu):
        menu.delete(0, tk.END)
        for name in self.presets.keys():
            menu.add_command(label=name, command=lambda n=name: self.apply_preset(n))

    def _fill_palette_menu(self, menu):
        menu.delete(0, tk.END)
        for name in PALETTES.keys():
            menu.add_command(label=name, command=lambda n=name: self.switch_palette(n))

    # ============================ UI 构建 ============================
    def setup_ui(self):
        if self.main_frame:
            self.main_frame.destroy()
            self.main_frame = None

        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开图片...", command=self.load_single_image, accelerator="Ctrl+O")
        file_menu.add_command(label="打开文件夹...", command=self.load_batch_folder)
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="最近打开", menu=self.recent_menu)
        file_menu.add_separator()
        file_menu.add_command(label="保存", command=self.save_image, accelerator="Ctrl+S")
        file_menu.add_command(label="另存为", command=self.save_image_as)
        file_menu.add_command(label="全部保存", command=self.save_all)
        file_menu.add_separator()
        file_menu.add_command(label="重启", command=self.restart_app)
        file_menu.add_command(label="退出", command=self.on_close, accelerator="Ctrl+Q")

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="编辑像素画", command=self.open_editor, accelerator="Ctrl+E")
        edit_menu.add_command(label="重置缩放", command=self.reset_zoom)
        edit_menu.add_separator()

        self._preset_menu = tk.Menu(edit_menu, tearoff=0)
        self._preset_menu.configure(postcommand=lambda: self._fill_preset_menu(self._preset_menu))
        edit_menu.add_cascade(label="预设尺寸", menu=self._preset_menu)

        self._palette_menu = tk.Menu(edit_menu, tearoff=0)
        self._palette_menu.configure(postcommand=lambda: self._fill_palette_menu(self._palette_menu))
        edit_menu.add_cascade(label="色盘", menu=self._palette_menu)

        edit_menu.add_separator()
        edit_menu.add_command(label="首选项...", command=self.open_preferences, accelerator="Ctrl+,")

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="检查更新", command=self.check_update)
        help_menu.add_command(label="关于", command=self.show_about)

        self.root.bind_all("<Control-o>", lambda e: self.load_single_image())
        self.root.bind_all("<Control-s>", lambda e: self.save_image())
        self.root.bind_all("<Control-e>", lambda e: self.open_editor())
        self.root.bind_all("<Control-q>", lambda e: self.on_close())
        self.root.bind_all("<Control-comma>", lambda e: self.open_preferences())

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=8, fill=tk.BOTH, expand=True)

        file_row = tk.Frame(self.main_frame)
        file_row.pack(fill=tk.X, pady=(0, 5))
        tk.Button(file_row, text="选择图片", command=self.load_single_image, width=12).pack(side=tk.LEFT, padx=(0,5))
        tk.Button(file_row, text="批量处理", command=self.load_batch_folder, width=12).pack(side=tk.LEFT, padx=(0,5))
        self.file_label = tk.Label(file_row, text="未选择文件", anchor="w", relief="sunken")
        self.file_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        nav_frame = tk.Frame(self.main_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 5))
        self.prev_btn = tk.Button(nav_frame, text="上一张", command=self.prev_image, state=tk.DISABLED, width=10)
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.page_label = tk.Label(nav_frame, text="", fg="#888", font=("Arial", 11))
        self.page_label.pack(side=tk.LEFT)
        self.next_btn = tk.Button(nav_frame, text="下一张", command=self.next_image, state=tk.DISABLED, width=10)
        self.next_btn.pack(side=tk.LEFT, padx=(10, 0))
        self.save_batch_btn = tk.Button(nav_frame, text="保存当前", command=self.save_current_batch,
                                         state=tk.DISABLED, bg="#4CAF50", fg="white", width=10)
        self.save_batch_btn.pack(side=tk.RIGHT)

        param = tk.Frame(self.main_frame)
        param.pack(fill=tk.X, pady=(0, 8))

        tk.Label(param, text="预设:").pack(side=tk.LEFT)
        self.preset_var = tk.StringVar(value="自定义")
        self.preset_combo = ttk.Combobox(param, textvariable=self.preset_var,
                                         values=["自定义"] + list(self.presets.keys()),
                                         state="readonly", width=8)
        self.preset_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.preset_combo.bind("<<ComboboxSelected>>", self.on_preset_selected)

        tk.Label(param, text="块:").pack(side=tk.LEFT)
        self.block_var = tk.IntVar(value=12)
        block_from = int(self.dev.get("block_min", 2))
        block_to = int(self.dev.get("block_max", 40))
        if block_to <= block_from:
            block_to = block_from + 1
        self.block_scale = tk.Scale(param, from_=block_from, to=block_to, orient=tk.HORIZONTAL,
                                    variable=self.block_var, length=100, showvalue=0)
        self.block_scale.pack(side=tk.LEFT, padx=(0, 5))
        self.block_scale.bind("<MouseWheel>", lambda e: self.on_scale_wheel(e, self.block_scale, self.block_var, self.block_label, self.on_block_changed))
        self.block_label = tk.Label(param, text="12", width=3)
        self.block_label.pack(side=tk.LEFT, padx=(0, 10))
        self.block_scale.config(command=lambda v: (self.block_label.config(text=v), self.on_block_changed()))

        tk.Label(param, text="颜色:").pack(side=tk.LEFT)
        self.color_var = tk.IntVar(value=16)
        color_from = int(self.dev.get("colors_min", 2))
        color_to = int(self.dev.get("colors_max", 64))
        if color_to <= color_from:
            color_to = color_from + 1
        self.color_scale = tk.Scale(param, from_=color_from, to=color_to, orient=tk.HORIZONTAL,
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

        tk.Button(param, text="编辑像素画", command=self.open_editor, width=12, bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(param, text="对比视图", command=self.open_comparison, width=12, bg="#9C27B0", fg="white").pack(side=tk.LEFT)

        display = tk.Frame(self.main_frame)
        display.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        display.grid_rowconfigure(0, weight=1)
        display.grid_columnconfigure(0, weight=1, uniform="preview")
        display.grid_columnconfigure(1, weight=1, uniform="preview")

        left = tk.LabelFrame(display, text="原图")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self._setup_canvas_with_scrollbar(left, "orig")

        right = tk.LabelFrame(display, text="像素画")
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self._setup_canvas_with_scrollbar(right, "res")

        for c in (self.orig_canvas, self.res_canvas):
            c.bind("<MouseWheel>", self.on_mousewheel)
            c.bind("<Double-Button-1>", self.reset_zoom)
            c.bind("<ButtonPress-1>", lambda e: self._start_pan(e))
            c.bind("<B1-Motion>", self._do_pan)
            c.bind("<ButtonRelease-1>", self._end_pan)
            c.bind("<Motion>", self._on_main_canvas_motion)
            c.bind("<Leave>", self._on_main_canvas_leave)

        self.root.bind("<Configure>", self.on_resize)

        bottom = tk.Frame(self.main_frame)
        bottom.pack(fill=tk.X, pady=(5, 0))

        self.save_btn = tk.Button(bottom, text="保存像素画", command=self.save_image,
                                  state=tk.DISABLED, bg="#2196F3", fg="white")
        self.save_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.svg_btn = tk.Button(bottom, text="导出 SVG", command=self.export_svg,
                                 state=tk.DISABLED, bg="#9C27B0", fg="white")
        self.svg_btn.pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(bottom, text="放大", command=self.zoom_in, width=4, bg="#333", fg="white").pack(side=tk.LEFT, padx=(0, 2))
        tk.Button(bottom, text="缩小", command=self.zoom_out, width=4, bg="#333", fg="white").pack(side=tk.LEFT, padx=(0, 2))
        tk.Button(bottom, text="重置", command=self.reset_zoom, width=4, bg="#333", fg="white").pack(side=tk.LEFT, padx=(0, 5))

        self.zoom_label = tk.Label(bottom, text="100%", fg="#888", font=("Arial", 10))
        self.zoom_label.pack(side=tk.LEFT, padx=(5, 10))

        self.status = tk.Label(bottom, text="", fg=self.dev.get("status_fg", "blue"), anchor="w")
        self.status.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

    def _setup_canvas_with_scrollbar(self, parent, name):
        frame = tk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        v_scroll = tk.Scrollbar(frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        h_scroll = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        canvas = tk.Canvas(frame, bg=self.dev.get("canvas_bg", "#1e1e1e"), highlightthickness=0,
                           xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if name == "orig":
            self.orig_canvas = canvas
            v_scroll.config(command=self._sync_scroll_orig_v)
            h_scroll.config(command=self._sync_scroll_orig_h)
        else:
            self.res_canvas = canvas
            v_scroll.config(command=self._sync_scroll_res_v)
            h_scroll.config(command=self._sync_scroll_res_h)

    def _on_main_canvas_motion(self, event):
        self._mouse_main_canvas = (event.x, event.y)

    def _on_main_canvas_leave(self, event):
        self._mouse_main_canvas = None

    # ============================ 滚动 / 平移 / 缩放 ============================
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

    def _start_pan(self, event):
        self.pan_data = {"x": event.x, "y": event.y,
                         "xview": self.orig_canvas.xview()[0],
                         "yview": self.orig_canvas.yview()[0]}

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
        step = float(self.settings.get("wheel_zoom_step", 0.1))
        zmin = float(self.dev.get("zoom_min", 0.1))
        zmax = float(self.dev.get("zoom_max", 10.0))
        if event.delta > 0:
            self.zoom_factor *= (1 + step)
        else:
            self.zoom_factor *= max(0.05, (1 - step))
        self.zoom_factor = max(zmin, min(zmax, self.zoom_factor))
        self.update_zoom_label()
        self.refresh_display()

    def zoom_in(self):
        factor = float(self.dev.get("zoom_in_factor", 1.15))
        zmax = float(self.dev.get("zoom_max", 10.0))
        self.zoom_factor = min(zmax, self.zoom_factor * factor)
        self.update_zoom_label()
        self.refresh_display()

    def zoom_out(self):
        factor = float(self.dev.get("zoom_out_factor", 0.85))
        zmin = float(self.dev.get("zoom_min", 0.1))
        self.zoom_factor = max(zmin, self.zoom_factor * factor)
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
            self.show_image(self.original_image, "orig")
        if self.result_image:
            self.show_image(self.result_image, "res")

    # ============================ 图片加载 ============================
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

    def _open_image(self, path):
        img = Image.open(path)
        if self.dev.get("exif_transpose", True):
            try:
                from PIL import ImageOps
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass
        return img

    def load_image_path(self, path):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        try:
            img = self._open_image(path)
            self.original_image = img.convert("RGBA")
            self.file_label.config(text=os.path.basename(path))
            self.result_image = None
            self.save_btn.config(state=tk.DISABLED)
            self.svg_btn.config(state=tk.DISABLED)
            self.current_display_size = (0, 0)
            self._cached_orig_display = None
            self._cached_res_display = None
            self.dirty = False
            if not self.is_batch_mode:
                self._add_recent(path)
            w, h = self.original_image.size
            self.update_status(f"已加载：{os.path.basename(path)} ({w}×{h})，自动转换中...")
            self.show_image(self.original_image, "orig")
            self.schedule_convert(immediate=True, mark_dirty=False)
            self._dev_log(f"加载图片：{path} 尺寸 {w}×{h}", LOG_INFO)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片：{e}")
            self._dev_log(f"打开图片失败：{e}", LOG_ERROR)

    def on_drop(self, event):
        try:
            files = self.root.tk.splitlist(event.data)
        except Exception:
            files = [event.data.strip('{}')]
        if files:
            path = files[0]
            if os.path.isfile(path):
                self.is_batch_mode = False
                self.batch_images = []
                self.batch_index = 0
                self.zoom_factor = 1.0
                self.update_zoom_label()
                self.update_nav_buttons()
                self.load_image_path(path)

    def load_batch_folder(self):
        folder = filedialog.askdirectory(title="选择包含图片的文件夹")
        if not folder:
            return

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
        self.file_label.config(text=f"{os.path.basename(folder)} ({len(files)}张)")
        self.zoom_factor = 1.0
        self.update_zoom_label()
        self.update_nav_buttons()
        self.load_image_path(files[0])
        self.update_status(f"已加载 {len(files)} 张图片，请翻页浏览或调整参数")
        self._dev_log(f"批量加载 {len(files)} 张：{folder}", LOG_INFO)

    def prev_image(self):
        if self.batch_index > 0:
            self.batch_index -= 1
            self.zoom_factor = 1.0
            self.update_zoom_label()
            self.load_image_path(self.batch_images[self.batch_index])
            self.update_nav_buttons()

    def next_image(self):
        if self.batch_index < len(self.batch_images)-1:
            self.batch_index += 1
            self.zoom_factor = 1.0
            self.update_zoom_label()
            self.load_image_path(self.batch_images[self.batch_index])
            self.update_nav_buttons()

    def update_nav_buttons(self):
        if self.is_batch_mode and self.batch_images:
            total = len(self.batch_images)
            self.prev_btn.config(state=tk.NORMAL if self.batch_index>0 else tk.DISABLED)
            self.next_btn.config(state=tk.NORMAL if self.batch_index<total-1 else tk.DISABLED)
            self.page_label.config(text=f"{self.batch_index+1} / {total}")
            self.save_batch_btn.config(state=tk.NORMAL)
        else:
            self.prev_btn.config(state=tk.DISABLED)
            self.next_btn.config(state=tk.DISABLED)
            self.page_label.config(text="")
            self.save_batch_btn.config(state=tk.DISABLED)

    # ============================ 最近打开 ============================
    def _add_recent(self, path):
        path = os.path.abspath(path)
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        max_n = max(1, int(self.dev.get("recent_max", 5)))
        self.recent_files = self.recent_files[:max_n]
        self._rebuild_recent_menu()

    def _rebuild_recent_menu(self):
        m = self.recent_menu
        m.delete(0, tk.END)
        if not self.recent_files:
            m.add_command(label="（无）", state=tk.DISABLED)
            return
        trunc = max(8, int(self.dev.get("recent_menu_truncate", 40)))
        for p in self.recent_files:
            if os.path.exists(p):
                base = os.path.basename(p)
                if len(base) > trunc:
                    base = base[:trunc - 3] + "..."
                m.add_command(label=base, command=lambda pp=p: self._open_recent(pp))
        m.add_separator()
        m.add_command(label="清空列表", command=self._clear_recent)

    def _open_recent(self, path):
        if not os.path.exists(path):
            messagebox.showwarning("提示", "文件不存在")
            self.recent_files.remove(path)
            self._rebuild_recent_menu()
            return
        self.is_batch_mode = False
        self.batch_images = []
        self.batch_index = 0
        self.zoom_factor = 1.0
        self.update_zoom_label()
        self.update_nav_buttons()
        self.load_image_path(path)

    def _clear_recent(self):
        self.recent_files = []
        self._rebuild_recent_menu()

    # ============================ 参数 / 转换 ============================
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
            self._save_image_to(self.result_image, save_path)
            self.dirty = False
            self.update_status(f"已保存：{os.path.basename(save_path)}", kind="success")
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
        if preset not in self.presets:
            return
        target_w, target_h = self.presets[preset]
        w, h = self.original_image.size
        cap = max(1, int(self._preset_new_block_cap))
        new_block = min(w//target_w, h//target_h, cap)
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

    def _process_image_core(self, img, block, colors, palette, dither_method=None):
        if dither_method is None:
            dither_method = self.settings.get("dither_method", "NONE")
        w, h = img.size
        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            rgb_img = Image.merge('RGB', (r, g, b))
            has_alpha = True
        else:
            rgb_img = img.convert('RGB')
            has_alpha = False

        bw, bh = max(1, w // block), max(1, h // block)
        small = rgb_img.resize((bw, bh), RESAMPLE_NEAREST)

        if palette:
            palette_colors = list(palette)
            if dither_method == "FLOYDSTEINBERG":
                pal_img = self._get_palette_image(palette_colors)
                small = small.quantize(palette=pal_img, dither=DITHER_FS).convert('RGB')
            elif dither_method in ("BAYER4", "BAYER8", "ATKINSON"):
                small = self._custom_dither(small, palette_colors, dither_method)
            else:
                pal_img = self._get_palette_image(palette_colors)
                small = small.quantize(palette=pal_img, dither=DITHER_NONE).convert('RGB')
        else:
            if colors < 256:
                method_key = self.settings.get("quantize_method", "MEDIANCUT")
                method_map = {
                    "MEDIANCUT": Image.MEDIANCUT,
                    "MAXCOVERAGE": Image.MAXCOVERAGE,
                    "FASTOCTREE": Image.FASTOCTREE,
                }
                method = method_map.get(method_key, Image.MEDIANCUT)
                if dither_method == "FLOYDSTEINBERG":
                    small = small.quantize(colors=colors, method=method, dither=DITHER_FS).convert('RGB')
                elif dither_method in ("BAYER4", "BAYER8", "ATKINSON"):
                    quantized = small.quantize(colors=colors, method=method, dither=DITHER_NONE)
                    pal = quantized.getpalette()
                    if pal is None:
                        small = quantized.convert('RGB')
                    else:
                        palette_colors = [tuple(pal[i:i+3]) for i in range(0, len(pal), 3)][:colors]
                        small = self._custom_dither(small, palette_colors, dither_method)
                else:
                    small = small.quantize(colors=colors, method=method, dither=DITHER_NONE).convert('RGB')

        result_rgb = small.resize((w, h), RESAMPLE_NEAREST)

        if has_alpha:
            small_a = a.resize((bw, bh), RESAMPLE_NEAREST)
            result_a = small_a.resize((w, h), RESAMPLE_NEAREST)
            result = Image.merge('RGBA', (*result_rgb.split(), result_a))
        else:
            result = result_rgb

        small_pixels = small.load()
        grid_colors = [[small_pixels[x, y] for x in range(bw)] for y in range(bh)]
        return result, bw, bh, grid_colors

    def process_image(self, img, block, colors, palette, save_editor=True):
        result, bw, bh, gcolors = self._process_image_core(img, block, colors, palette)
        if save_editor:
            self.grid_w, self.grid_h = bw, bh
            self.grid_colors = gcolors
        return result

    def _nearest_color(self, r, g, b, palette_colors):
        if self.dev.get("nearest_use_weighted", False):
            wr = float(self.dev.get("nearest_weight_r", 2.0))
            wg = float(self.dev.get("nearest_weight_g", 4.0))
            wb = float(self.dev.get("nearest_weight_b", 3.0))
        else:
            wr = wg = wb = 1.0
        best = palette_colors[0]
        best_dist = wr*(r-best[0])**2 + wg*(g-best[1])**2 + wb*(b-best[2])**2
        for c in palette_colors[1:]:
            d = wr*(r-c[0])**2 + wg*(g-c[1])**2 + wb*(b-c[2])**2
            if d < best_dist:
                best_dist = d
                best = c
        return best

    def _custom_dither(self, img, palette_colors, method):
        if not palette_colors:
            return img.convert('RGB')
        if method == "BAYER4":
            return self._bayer_dither(img, palette_colors, BAYER_4)
        if method == "BAYER8":
            return self._bayer_dither(img, palette_colors, BAYER_8)
        if method == "ATKINSON":
            return self._atkinson_dither(img, palette_colors)
        return img.convert('RGB')

    def _bayer_dither(self, img, palette_colors, matrix):
        pixels = img.load()
        w, h = img.size
        n = len(matrix)
        scale = n * n
        spread = 255.0 / (max(2, len(palette_colors)) ** 0.5)
        spread *= float(self.dev.get("bayer_spread_multiplier", 1.0))
        out = Image.new('RGB', (w, h))
        out_pixels = out.load()
        cache = {}
        for y in range(h):
            for x in range(w):
                r, g, b = pixels[x, y]
                threshold = (matrix[y % n][x % n] + 0.5) / scale - 0.5
                offset = threshold * spread
                nr = max(0, min(255, r + offset))
                ng = max(0, min(255, g + offset))
                nb = max(0, min(255, b + offset))
                key = (int(nr), int(ng), int(nb))
                c = cache.get(key)
                if c is None:
                    c = self._nearest_color(nr, ng, nb, palette_colors)
                    cache[key] = c
                out_pixels[x, y] = c
        return out

    def _atkinson_dither(self, img, palette_colors):
        pixels = img.load()
        w, h = img.size
        err = [[[0.0, 0.0, 0.0] for _ in range(w)] for _ in range(h)]
        out = Image.new('RGB', (w, h))
        out_pixels = out.load()
        cache = {}
        neighbors = ((1, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (0, 2))
        scale = float(self.dev.get("atkinson_error_scale", 1.0))
        for y in range(h):
            for x in range(w):
                r, g, b = pixels[x, y]
                er, eg, eb = err[y][x]
                nr = max(0, min(255, r + er))
                ng = max(0, min(255, g + eg))
                nb = max(0, min(255, b + eb))
                key = (int(nr), int(ng), int(nb))
                c = cache.get(key)
                if c is None:
                    c = self._nearest_color(nr, ng, nb, palette_colors)
                    cache[key] = c
                out_pixels[x, y] = c
                dr = (nr - c[0]) * scale
                dg = (ng - c[1]) * scale
                db = (nb - c[2]) * scale
                for dx, dy in neighbors:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        err[ny][nx][0] += dr / 8
                        err[ny][nx][1] += dg / 8
                        err[ny][nx][2] += db / 8
        return out

    def schedule_convert(self, immediate=False, mark_dirty=True):
        if self.original_image is None:
            return
        self._mark_dirty_on_convert = mark_dirty
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        delay = max(0, int(self.dev.get("convert_debounce_ms", 150)))
        if immediate:
            self.do_convert()
        else:
            self.after_id = self.root.after(delay, self.do_convert)

    def do_convert(self):
        self.after_id = None
        if self.original_image is None or self._closing:
            return
        if self._converting:
            self._pending_convert = True
            return
        self._start_convert()

    def _start_convert(self):
        if self.original_image is None or self._closing:
            return
        block = self.block_var.get()
        colors = self.color_var.get()
        palette = PALETTES.get(self.palette_var.get())
        dither = self.settings.get("dither_method", "NONE")
        mark_dirty = self._mark_dirty_on_convert
        try:
            img = self.original_image.copy()
        except Exception:
            return

        self._converting = True
        self.update_status(f"正在转换（块 {block} | 颜色 {colors}）...")
        start_ts = time.time()
        self._dev_log(f"转换开始 块={block} 颜色={colors} 抖动={dither}", LOG_DEBUG)

        def worker():
            result = None
            gw = gh = 0
            gcolors = None
            err = None
            try:
                result, gw, gh, gcolors = self._process_image_core(
                    img, block, colors, palette, dither)
            except Exception as e:
                err = e
            if self._closing:
                return
            try:
                self.root.after(0, lambda: self._on_convert_done(
                    result, gw, gh, gcolors, mark_dirty, block, colors, start_ts, err))
            except tk.TclError:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _on_convert_done(self, result, gw, gh, gcolors, mark_dirty, block, colors, start_ts, error):
        if self._closing:
            return
        self._converting = False
        if error is not None:
            self._dev_log(f"转换失败：{error}", LOG_ERROR)
            if self._pending_convert:
                self._pending_convert = False
                self._start_convert()
                return
            messagebox.showerror("转换错误", str(error))
            self.update_status("转换失败", kind="error")
            return
        if self._pending_convert:
            self._pending_convert = False
            self._start_convert()
            return
        self.grid_w, self.grid_h = gw, gh
        self.grid_colors = gcolors
        self.result_image = result
        self._cached_res_display = None
        self.show_image(result, "res")
        self.save_btn.config(state=tk.NORMAL)
        self.svg_btn.config(state=tk.NORMAL)
        if mark_dirty:
            self.dirty = True
        elapsed = time.time() - start_ts
        self._dev_log(f"转换完成 {gw}×{gh} 耗时 {elapsed*1000:.0f}ms", LOG_DEBUG)
        status = f"块 {block} | 颜色 {colors} | 网格 {gw}×{gh}"
        if self.dev.get("show_convert_time", True):
            status += f" | {elapsed*1000:.0f}ms"
        self.update_status(status)

    def _get_resample(self, target):
        if target == "res":
            key = self.settings.get("resample_result", "NEAREST")
        else:
            key = self.settings.get("resample_original", "BILINEAR")
        return {
            "NEAREST": RESAMPLE_NEAREST,
            "BILINEAR": RESAMPLE_BILINEAR,
            "BICUBIC": RESAMPLE_BICUBIC,
            "LANCZOS": RESAMPLE_LANCZOS,
        }.get(key, RESAMPLE_BILINEAR)

    def show_image(self, pil_img, target, retry=5):
        if pil_img is None:
            return
        canvas = self.orig_canvas if target == "orig" else self.res_canvas
        cw, ch = canvas.winfo_width(), canvas.winfo_height()
        if cw < 10 or ch < 10:
            if retry > 0:
                self.root.after(50, lambda: self.show_image(pil_img, target, retry - 1))
            return

        w, h = pil_img.size
        scale_fit = min(cw / w, ch / h, 1.0) if (cw > 0 and ch > 0) else 1.0
        final_scale = scale_fit * self.zoom_factor
        new_w, new_h = int(w * final_scale), int(h * final_scale)
        if new_w < 1 or new_h < 1:
            return

        cache = self._cached_orig_display if target == "orig" else self._cached_res_display
        if cache and cache[1] == (new_w, new_h):
            canvas.delete("all")
            canvas.create_image((cw - new_w)//2, (ch - new_h)//2, anchor=tk.NW, image=cache[0])
            canvas.config(scrollregion=(0, 0, new_w, new_h))
            return

        threshold = int(self.dev.get("smooth_resize_threshold", 2000))
        resample = self._get_resample(target)
        if threshold > 0 and target == "orig" and (w > threshold or h > threshold):
            resample = RESAMPLE_BILINEAR

        resized = pil_img.resize((new_w, new_h), resample)
        tk_img = ImageTk.PhotoImage(resized)
        canvas.delete("all")
        if new_w <= cw and new_h <= ch:
            canvas.create_image((cw - new_w)//2, (ch - new_h)//2, anchor=tk.NW, image=tk_img)
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
            self.refresh_display()

    # ============================ 对比视图 ============================
    def open_comparison(self):
        if self.original_image is None or self.result_image is None:
            messagebox.showwarning("提示", "请先生成像素画")
            return
        if self.compare_window is not None and self.compare_window.winfo_exists():
            self.compare_window.lift()
            return
        self.compare_window = tk.Toplevel(self.root)
        self.compare_window.title("对比视图")
        self.compare_window.geometry("900x600")
        self.compare_window.minsize(600, 400)
        self.compare_window.protocol("WM_DELETE_WINDOW", self._close_compare)

        orig = self.original_image.convert('RGB')
        res = self.result_image.convert('RGB')
        split_pos = 0.5
        dragging = False

        canvas_frame = tk.Frame(self.compare_window)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        compare_canvas = tk.Canvas(canvas_frame, bg=self.dev.get("canvas_bg", "#1e1e1e"), highlightthickness=0)
        compare_canvas.pack(fill=tk.BOTH, expand=True)
        compare_canvas.compare_xoff = 0
        compare_canvas.compare_nw = 1

        def draw():
            cw, ch = compare_canvas.winfo_width(), compare_canvas.winfo_height()
            if cw < 10 or ch < 10:
                compare_canvas.after(50, draw)
                return
            w, h = orig.size
            scale = min(cw / w, ch / h, 1.0)
            nw, nh = int(w * scale), int(h * scale)
            if nw < 1 or nh < 1:
                return
            o = orig.resize((nw, nh), RESAMPLE_BILINEAR)
            r = res.resize((nw, nh), RESAMPLE_BILINEAR)
            split_x = int(max(0, min(nw, split_pos * nw)))
            composed = o.copy()
            if split_x < nw:
                composed.paste(r.crop((split_x, 0, nw, nh)), (split_x, 0))
            self.compare_tk = ImageTk.PhotoImage(composed)
            compare_canvas.delete("all")
            xoff, yoff = (cw - nw)//2, (ch - nh)//2
            compare_canvas.create_image(xoff, yoff, anchor=tk.NW, image=self.compare_tk)
            compare_canvas.create_line(xoff + split_x, yoff, xoff + split_x, yoff + nh,
                                       fill="white", width=2)
            rr = 10
            compare_canvas.create_oval(xoff + split_x - rr, yoff + nh//2 - rr,
                                       xoff + split_x + rr, yoff + nh//2 + rr,
                                       fill="white", outline="#2196F3", width=2)
            compare_canvas.create_text(xoff + split_x, yoff + 20,
                                       text=f"{int(split_pos * 100)}%", fill="white",
                                       font=("Arial", 12, "bold"))
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
        tk.Label(bottom_frame, text="原图", fg="#888").pack(side=tk.LEFT, padx=(0, 10))
        slider = tk.Scale(bottom_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=400)
        slider.set(50)
        slider.pack(side=tk.LEFT, padx=10)

        def slider_update(val):
            nonlocal split_pos
            split_pos = float(val) / 100
            draw()
        slider.config(command=slider_update)
        tk.Label(bottom_frame, text="像素画", fg="#888").pack(side=tk.LEFT, padx=(10, 0))
        tk.Button(bottom_frame, text="重置", command=lambda: (slider.set(50), slider_update("50")),
                  width=6, bg="#333", fg="white").pack(side=tk.RIGHT, padx=(0, 5))
        tk.Button(bottom_frame, text="关闭", command=self._close_compare,
                  width=6, bg="#555", fg="white").pack(side=tk.RIGHT)

        self.compare_window.after(100, draw)

    def _close_compare(self):
        if self.compare_window is not None:
            self.compare_window.destroy()
            self.compare_window = None

    # ============================ 导出 / 保存 ============================
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
            parts = [f'<?xml version="1.0" encoding="UTF-8"?>\n'
                     f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*ps}" height="{h*ps}" '
                     f'viewBox="0 0 {w*ps} {h*ps}">\n'
                     f'  <rect width="100%" height="100%" fill="#ffffff"/>\n']
            append = parts.append
            for y in range(h):
                for x in range(w):
                    r, g, b = pixels[x, y]
                    append(f'  <rect x="{x*ps}" y="{y*ps}" width="{ps}" height="{ps}" '
                           f'fill="#{r:02x}{g:02x}{b:02x}" stroke="#eeeeee" stroke-width="0.5"/>\n')
            append('</svg>')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(''.join(parts))
            self.update_status(f"SVG 已导出：{os.path.basename(path)}", kind="success")
            self._dev_log(f"导出 SVG：{path}", LOG_INFO)
        except Exception as e:
            messagebox.showerror("导出 SVG 错误", str(e))
            self._dev_log(f"导出 SVG 失败：{e}", LOG_ERROR)

    def save_image(self):
        if self.result_image is None:
            return
        path = filedialog.asksaveasfilename(**self._get_save_kwargs())
        if path:
            try:
                self._save_image_to(self.result_image, path)
                self.dirty = False
                self.update_status(f"已保存：{os.path.basename(path)}", kind="success")
            except Exception as e:
                messagebox.showerror("保存错误", str(e))

    def save_image_as(self):
        if self.result_image is None:
            messagebox.showwarning("提示", "没有可保存的像素画")
            return
        path = filedialog.asksaveasfilename(**self._get_save_kwargs())
        if path:
            try:
                self._save_image_to(self.result_image, path)
                self.dirty = False
                self.update_status(f"已保存：{os.path.basename(path)}", kind="success")
            except Exception as e:
                messagebox.showerror("保存错误", str(e))

    def save_all(self):
        if self.original_image is None:
            messagebox.showwarning("提示", "没有图片可保存")
            return
        if not self.is_batch_mode:
            self.save_image_as()
            return
        if not self.batch_images:
            messagebox.showinfo("提示", "没有批量图片")
            return

        block = self.block_var.get()
        colors = self.color_var.get()
        palette = PALETTES.get(self.palette_var.get())
        dither = self.settings.get("dither_method", "NONE")

        folder = os.path.dirname(self.batch_images[0])
        output_folder = os.path.join(folder, "pixel_output")
        os.makedirs(output_folder, exist_ok=True)
        total = len(self.batch_images)

        progress_win = tk.Toplevel(self.root)
        progress_win.title("批量保存")
        progress_win.geometry("350x120")
        progress_win.resizable(False, False)
        progress_win.transient(self.root)
        tk.Label(progress_win, text=f"正在保存 {total} 张图片...", font=("Arial", 11)).pack(pady=10)
        progress_bar = ttk.Progressbar(progress_win, length=300, maximum=total, mode='determinate')
        progress_bar.pack(pady=5)
        info_label = tk.Label(progress_win, text=f"0 / {total}")
        info_label.pack()

        from concurrent.futures import ThreadPoolExecutor
        threads = max(1, int(self.dev.get("batch_threads", 4)))
        poll_ms = max(50, int(self.dev.get("batch_poll_ms", 200)))
        executor = ThreadPoolExecutor(max_workers=threads)
        futures = [executor.submit(self._save_one_image, p, block, colors, palette, dither)
                   for p in self.batch_images]

        def poll():
            done = sum(1 for f in futures if f.done())
            progress_bar['value'] = done
            info_label.config(text=f"{done} / {total}")
            if done >= total:
                executor.shutdown(wait=False)
                if progress_win.winfo_exists():
                    progress_win.destroy()
                self.dirty = False
                self.update_status(f"全部保存完成！共 {total} 张图片", kind="success")
                messagebox.showinfo("完成", f"全部保存完成！\n共保存 {total} 张图片\n位置：{output_folder}")
                self._dev_log(f"批量保存完成：{total} 张 -> {output_folder}", LOG_INFO)
            elif progress_win.winfo_exists():
                progress_win.after(poll_ms, poll)
            else:
                executor.shutdown(wait=False)

        poll()

    def _save_one_image(self, img_path, block, colors, palette, dither_method):
        try:
            img = self._open_image(img_path).convert("RGBA")
            result, _, _, _ = self._process_image_core(img, block, colors, palette, dither_method)
            if result:
                folder = os.path.dirname(img_path)
                output_folder = os.path.join(folder, "pixel_output")
                os.makedirs(output_folder, exist_ok=True)
                base = os.path.splitext(os.path.basename(img_path))[0]
                save_path = os.path.join(output_folder, f"{base}_pixel.png")
                self._save_image_to(result, save_path)
        except Exception as e:
            self._dev_log(f"处理 {img_path} 失败：{e}", LOG_ERROR)

    # ============================ 编辑器 ============================
    def open_editor(self):
        if self._converting:
            messagebox.showinfo("提示", "正在转换中，请稍候再打开编辑器")
            return
        if self.result_image is None:
            messagebox.showwarning("提示", "请先生成像素画")
            return
        if not self.grid_colors:
            messagebox.showwarning("提示", "当前没有可编辑的网格数据")
            return
        if self.edit_window is not None and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return
        self.edit_window = tk.Toplevel(self.root)
        self._update_editor_title()
        self.edit_window.geometry("780x670")
        self.edit_window.minsize(560, 460)
        self.edit_window.protocol("WM_DELETE_WINDOW", self._close_editor)
        self.edit_window.bind("<Escape>", lambda e: self._close_editor())

        limit = int(self.settings.get("undo_limit", 100))
        self.undo_stack = deque(maxlen=limit)
        self.redo_stack = deque(maxlen=limit)
        self.edit_tool = "brush"
        self.current_color = (255, 0, 0)
        self.edit_selection = []
        self.edit_selection_start = None
        self.selection_rect_id = None
        self.edit_clipboard = []
        self.cell_items = []
        self._stroke_active = False
        self.edit_cell_size = 1
        self.edit_offset_x = 0
        self.edit_offset_y = 0
        self._editor_dirty = False
        self._mouse_editor_grid = None

        self.show_grid_lines = bool(self.settings.get("default_show_grid", True))

        grid_data = self.grid_colors
        self.edit_grid_w = len(grid_data[0]) if grid_data else 0
        self.edit_grid_h = len(grid_data)
        self.edit_grid = [row[:] for row in grid_data]

        top = tk.Frame(self.edit_window); top.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(top, text="工具:").pack(side=tk.LEFT)
        tools = tk.Frame(top); tools.pack(side=tk.LEFT, padx=5)
        default_tool = self.settings.get("default_tool", "画笔")
        if default_tool not in ["画笔", "橡皮", "框选", "填充", "吸管"]:
            default_tool = "画笔"
        self.tool_var = tk.StringVar(value=default_tool)
        for t, label in [("画笔", "画笔"), ("橡皮", "橡皮"), ("框选", "框选"), ("填充", "填充"), ("吸管", "吸管")]:
            tk.Radiobutton(tools, text=label, variable=self.tool_var, value=t, command=self.set_tool).pack(side=tk.LEFT, padx=2)
        self.edit_tool = default_tool
        tk.Label(top, text="  ").pack(side=tk.LEFT)
        self.color_preview = tk.Canvas(top, width=30, height=30, bg="#FF0000", highlightthickness=2)
        self.color_preview.pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="选择颜色", command=self.choose_color).pack(side=tk.LEFT, padx=5)
        tk.Label(top, text="  ").pack(side=tk.LEFT)
        tk.Button(top, text="撤销", command=self.editor_undo).pack(side=tk.LEFT, padx=2)
        tk.Button(top, text="重做", command=self.editor_redo).pack(side=tk.LEFT, padx=2)
        tk.Button(top, text="复制", command=self.editor_copy).pack(side=tk.LEFT, padx=2)
        tk.Button(top, text="粘贴", command=self.editor_paste).pack(side=tk.LEFT, padx=2)
        tk.Button(top, text="清空选择", command=self.editor_clear_selection).pack(side=tk.LEFT, padx=2)
        tk.Button(top, text="保存并关闭", command=self.save_editor).pack(side=tk.RIGHT, padx=5)

        hint_frame = tk.Frame(self.edit_window); hint_frame.pack(fill=tk.X, padx=10, pady=(0,5))
        self.hint_label = tk.Label(hint_frame,
                                   text="提示：画笔：点击修改 | 框选：拖拽选多个 | 填充：点击区域自动填色 | 吸管：拾取颜色",
                                   fg="#888", font=("Arial",9))
        self.hint_label.pack(side=tk.LEFT)
        self.coord_label = tk.Label(hint_frame, text="", fg="#2196F3", font=("Consolas", 9))
        self.coord_label.pack(side=tk.RIGHT)

        opt_frame = tk.Frame(self.edit_window); opt_frame.pack(fill=tk.X, padx=10)
        self.grid_lines_var = tk.BooleanVar(value=self.show_grid_lines)
        tk.Checkbutton(opt_frame, text="显示网格线", variable=self.grid_lines_var,
                       command=self.toggle_grid_lines).pack(side=tk.LEFT)

        canvas_frame = tk.Frame(self.edit_window); canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.edit_canvas = tk.Canvas(canvas_frame, bg=self.dev.get("editor_canvas_bg", "#1e1e1e"), highlightthickness=0)
        self.edit_canvas.pack(fill=tk.BOTH, expand=True)
        self.edit_canvas.bind("<Configure>", self.draw_edit_grid)
        self.edit_canvas.bind("<Button-1>", self.on_edit_click)
        self.edit_canvas.bind("<B1-Motion>", self.on_edit_drag)
        self.edit_canvas.bind("<ButtonRelease-1>", self.on_edit_release)
        self.edit_canvas.bind("<Motion>", self.on_edit_motion)
        self.edit_canvas.bind("<Leave>", lambda e: setattr(self, "_mouse_editor_grid", None))
        self.edit_canvas.bind("<KeyPress>", self.on_edit_key)
        self.edit_canvas.bind("<Control-z>", lambda e: self.editor_undo())
        self.edit_canvas.bind("<Control-Z>", lambda e: self.editor_undo())
        self.edit_canvas.bind("<Control-y>", lambda e: self.editor_redo())
        self.edit_canvas.bind("<Control-Y>", lambda e: self.editor_redo())
        self.edit_canvas.bind("<Delete>", lambda e: self.editor_clear_selection())
        self.edit_canvas.focus_set()
        self.update_hint()
        self.draw_edit_grid()
        self._dev_log(f"编辑器打开 {self.edit_grid_w}×{self.edit_grid_h}", LOG_INFO)

    def _close_editor(self):
        if self._editor_dirty and self.edit_grid_w > 0 and self.edit_grid_h > 0:
            ok = messagebox.askyesno(
                "未应用的修改",
                "编辑器中有尚未应用的修改，直接关闭将丢弃这些修改。\n\n确定要关闭吗？"
            )
            if not ok:
                return
        if self.edit_window is not None:
            self.edit_window.destroy()
            self.edit_window = None
        self._editor_dirty = False
        self._mouse_editor_grid = None

    def toggle_grid_lines(self):
        self.show_grid_lines = self.grid_lines_var.get()
        outline = self.settings.get("grid_line_color", "#333333") if self.show_grid_lines else ""
        for row in self.cell_items:
            for item in row:
                if item is not None:
                    self.edit_canvas.itemconfig(item, outline=outline)

    def set_tool(self):
        self.edit_tool = self.tool_var.get()
        if self.edit_tool != "框选":
            self.clear_selection()
        self.update_hint()

    def update_hint(self):
        hints = {
            "画笔": "点击像素块修改颜色",
            "橡皮": "点击像素块擦除",
            "框选": "拖拽选中，方向键移动",
            "填充": "点击区域自动填充",
            "吸管": "拾取像素颜色"
        }
        self.hint_label.config(text=f"提示：{hints.get(self.edit_tool, '')}")

    def on_edit_motion(self, event):
        pos = self.get_grid_pos(event.x, event.y)
        self._mouse_editor_grid = pos
        if not getattr(self, "cell_items", None):
            return
        if not self.dev.get("show_hover_coords", True):
            self.coord_label.config(text="")
            return
        if pos:
            gx, gy = pos
            col = self.edit_grid[gy][gx]
            self.coord_label.config(text=f"({gx},{gy})  #{col[0]:02x}{col[1]:02x}{col[2]:02x}")
        else:
            self.coord_label.config(text="")

    def choose_color(self):
        color = self._pick_color(title="选择颜色", initialcolor=self.current_color)
        if color and color[0]:
            self.current_color = tuple(int(c) for c in color[0])
            self.color_preview.config(bg=self._grid_to_hex(self.current_color))

    def _grid_to_hex(self, col):
        return f"#{col[0]:02x}{col[1]:02x}{col[2]:02x}"

    def draw_edit_grid(self, event=None):
        if self.edit_grid_w == 0 or self.edit_grid_h == 0:
            return
        cw, ch = self.edit_canvas.winfo_width(), self.edit_canvas.winfo_height()
        if cw < 10 or ch < 10:
            return
        cell = min(cw / self.edit_grid_w, ch / self.edit_grid_h)
        ox = (cw - cell * self.edit_grid_w) / 2
        oy = (ch - cell * self.edit_grid_h) / 2
        self.edit_cell_size, self.edit_offset_x, self.edit_offset_y = cell, ox, oy
        self.edit_canvas.delete("all")
        self.cell_items = [[None] * self.edit_grid_w for _ in range(self.edit_grid_h)]

        threshold = int(self.dev.get("editor_grid_render_threshold", 0))
        if threshold > 0 and (self.edit_grid_w * self.edit_grid_h) > threshold:
            outline = ""
        else:
            outline = self.settings.get("grid_line_color", "#333333") if self.show_grid_lines else ""

        for y in range(self.edit_grid_h):
            for x in range(self.edit_grid_w):
                x0, y0 = ox + x * cell, oy + y * cell
                self.cell_items[y][x] = self.edit_canvas.create_rectangle(
                    x0, y0, x0 + cell, y0 + cell,
                    fill=self._grid_to_hex(self.edit_grid[y][x]),
                    outline=outline, width=1)
        self._draw_selection_overlay()

    def _update_cell(self, gx, gy):
        if not self.cell_items:
            return
        if 0 <= gy < len(self.cell_items) and 0 <= gx < len(self.cell_items[gy]):
            item = self.cell_items[gy][gx]
            if item is not None:
                self.edit_canvas.itemconfig(item, fill=self._grid_to_hex(self.edit_grid[gy][gx]))

    def _draw_selection_overlay(self):
        self.edit_canvas.delete("selection_overlay")
        sel_color = self.dev.get("editor_selection_color", "#00FF00")
        for sx, sy in self.edit_selection:
            x0 = self.edit_offset_x + sx * self.edit_cell_size
            y0 = self.edit_offset_y + sy * self.edit_cell_size
            self.edit_canvas.create_rectangle(
                x0, y0, x0 + self.edit_cell_size, y0 + self.edit_cell_size,
                outline=sel_color, width=3, tags="selection_overlay")

    def get_grid_pos(self, x, y):
        rx, ry = x - self.edit_offset_x, y - self.edit_offset_y
        if rx < 0 or ry < 0:
            return None
        gx, gy = int(rx / self.edit_cell_size), int(ry / self.edit_cell_size)
        if gx >= self.edit_grid_w or gy >= self.edit_grid_h:
            return None
        return (gx, gy)

    def _push_undo(self):
        self.undo_stack.append([row[:] for row in self.edit_grid])
        self.redo_stack.clear()
        self._editor_dirty = True

    def editor_undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append([row[:] for row in self.edit_grid])
        self.edit_grid = self.undo_stack.pop()
        self._stroke_active = False
        self._editor_dirty = True
        self.draw_edit_grid()

    def editor_redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append([row[:] for row in self.edit_grid])
        self.edit_grid = self.redo_stack.pop()
        self._stroke_active = False
        self._editor_dirty = True
        self.draw_edit_grid()

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
            self.color_preview.config(bg=self._grid_to_hex(col))
            self.update_hint()
            return
        if self.edit_tool == "框选":
            self.edit_selection_start = pos
            self.clear_selection()
            return
        self._stroke_active = False
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
            drag_color = self.dev.get("editor_drag_color", "#00FF00")
            self.selection_rect_id = self.edit_canvas.create_rectangle(x0, y0, x1, y1,
                                                                       outline=drag_color, width=2, dash=(4,4))
            return
        if self.edit_tool in ["画笔", "橡皮"]:
            if not self.dev.get("continuous_drag_draw", True):
                if self._stroke_active:
                    return
            self.edit_pixel_at(pos[0], pos[1])

    def on_edit_release(self, event):
        self._stroke_active = False
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
            if self.selection_rect_id:
                self.edit_canvas.delete(self.selection_rect_id)
                self.selection_rect_id = None
            self._draw_selection_overlay()

    def edit_pixel_at(self, gx, gy):
        size = max(1, int(self.settings.get("brush_size", 1)))
        half = size // 2
        if self.edit_tool == "橡皮":
            color = tuple(self.settings.get("eraser_color", [128, 128, 128]))
        else:
            color = self.current_color

        to_change = []
        for yy in range(gy - half, gy - half + size):
            for xx in range(gx - half, gx - half + size):
                if 0 <= xx < self.edit_grid_w and 0 <= yy < self.edit_grid_h:
                    if self.edit_grid[yy][xx] != color:
                        to_change.append((xx, yy))

        if not to_change:
            return
        if not self._stroke_active:
            self._push_undo()
            self._stroke_active = True
        for xx, yy in to_change:
            self.edit_grid[yy][xx] = color
            self._update_cell(xx, yy)

    def flood_fill(self, sx, sy):
        target = self.edit_grid[sy][sx]
        fill = self.current_color
        if target == fill:
            return
        self._push_undo()
        q = deque([(sx, sy)])
        visited = {(sx, sy)}
        while q:
            x, y = q.popleft()
            if not (0 <= x < self.edit_grid_w and 0 <= y < self.edit_grid_h):
                continue
            if self.edit_grid[y][x] != target:
                continue
            self.edit_grid[y][x] = fill
            self._update_cell(x, y)
            for dx, dy in ((1,0), (-1,0), (0,1), (0,-1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.edit_grid_w and 0 <= ny < self.edit_grid_h:
                    if (nx, ny) not in visited and self.edit_grid[ny][nx] == target:
                        visited.add((nx, ny))
                        q.append((nx, ny))

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
        self._push_undo()
        ax, ay = self.edit_selection[0]
        minx = min(x for x, y, c in self.edit_clipboard)
        miny = min(y for x, y, c in self.edit_clipboard)
        for x, y, c in self.edit_clipboard:
            tx, ty = ax + (x - minx), ay + (y - miny)
            if 0 <= tx < self.edit_grid_w and 0 <= ty < self.edit_grid_h:
                self.edit_grid[ty][tx] = c
                self._update_cell(tx, ty)

    def editor_clear_selection(self):
        if not self.edit_selection:
            return
        self._push_undo()
        for x, y in self.edit_selection:
            self.edit_grid[y][x] = (128, 128, 128)
            self._update_cell(x, y)
        self.edit_selection.clear()
        self._draw_selection_overlay()

    def clear_selection(self):
        self.edit_selection.clear()
        self.edit_selection_start = None
        if self.selection_rect_id:
            self.edit_canvas.delete(self.selection_rect_id)
            self.selection_rect_id = None
        self.edit_canvas.delete("selection_overlay")
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
            if not (0 <= nx < self.edit_grid_w and 0 <= ny < self.edit_grid_h):
                return
            new_sel.append((nx, ny))
        self._push_undo()
        old = [row[:] for row in self.edit_grid]
        for x, y in self.edit_selection:
            self.edit_grid[y][x] = (128, 128, 128)
        for i, (x, y) in enumerate(self.edit_selection):
            nx, ny = new_sel[i]
            self.edit_grid[ny][nx] = old[y][x]
        affected = set(self.edit_selection) | set(new_sel)
        self.edit_selection = new_sel
        for (x, y) in affected:
            self._update_cell(x, y)
        self._draw_selection_overlay()

    def save_editor(self):
        if self.edit_grid_w == 0 or self.edit_grid_h == 0:
            return
        small_img = Image.new('RGB', (self.edit_grid_w, self.edit_grid_h))
        flat = [self.edit_grid[y][x]
                for y in range(self.edit_grid_h)
                for x in range(self.edit_grid_w)]
        small_img.putdata(flat)
        if self.result_image:
            w, h = self.result_image.size
            new_result = small_img.resize((w, h), RESAMPLE_NEAREST)
            if self.result_image.mode == 'RGBA':
                r, g, b = new_result.split()
                _, _, _, a = self.result_image.split()
                new_result = Image.merge('RGBA', (r, g, b, a))
            self.result_image = new_result
            self.grid_colors = [row[:] for row in self.edit_grid]
            self._cached_res_display = None
            self.show_image(new_result, "res")
            self.dirty = True
            self._editor_dirty = False
            self.update_status("编辑已应用", kind="success")
            self._dev_log("编辑器已应用修改", LOG_INFO)
        self._close_editor()

    # ============================ 监视窗口 ============================
    def toggle_watch(self, event=None):
        if self._watch_window is not None and self._watch_window.winfo_exists():
            self._close_watch()
        else:
            self._open_watch()
        return "break"

    def _open_watch(self):
        win = tk.Toplevel(self.root)
        win.title("调试监视")
        win.geometry("480x600")
        win.minsize(380, 400)
        win.protocol("WM_DELETE_WINDOW", self._close_watch)

        header = tk.Label(win, text="实时状态监视  (F12 关闭)", font=("Arial", 10, "bold"), anchor="w")
        header.pack(fill=tk.X, padx=8, pady=(8, 4))

        btns = tk.Frame(win)
        btns.pack(fill=tk.X, padx=8, pady=(0, 6))
        tk.Button(btns, text="刷新", command=self._update_watch, width=8).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(btns, text="复制", command=self._watch_copy, width=8).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(btns, text="关闭", command=self._close_watch, width=8).pack(side=tk.RIGHT)

        text_frame = tk.Frame(win)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        text = tk.Text(text_frame, font=("Consolas", 9), bg="#1e1e1e", fg="#e0e0e0",
                       insertbackground="#e0e0e0", wrap="word", relief="flat", borderwidth=0)
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._watch_window = win
        self._watch_text = text
        self._update_watch()

    def _close_watch(self):
        if self._watch_window is not None:
            try:
                self._watch_window.destroy()
            except Exception:
                pass
            self._watch_window = None
            self._watch_text = None

    def _watch_copy(self):
        if self._watch_text is None:
            return
        try:
            content = self._watch_text.get("1.0", "end-1c")
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.update_status("监视内容已复制到剪贴板", kind="success")
        except Exception as e:
            self._dev_log(f"复制监视内容失败：{e}", LOG_WARNING)

    def _update_watch(self):
        if self._watch_window is None or not self._watch_window.winfo_exists():
            return
        info = self._collect_watch_info()
        try:
            self._watch_text.config(state="normal")
            self._watch_text.delete("1.0", "end")
            self._watch_text.insert("1.0", info)
            self._watch_text.config(state="disabled")
        except Exception:
            return
        refresh_ms = max(100, int(self.dev.get("watch_refresh_ms", 250)))
        try:
            self._watch_window.after(refresh_ms, self._update_watch)
        except Exception:
            pass

    def _collect_watch_info(self):
        lines = []
        lines.append(f"版本: {self.dev.get('version_text', VERSION)}")
        lines.append(f"缩放: {self.zoom_factor:.3f}")
        lines.append(f"窗口: {self.root.winfo_width()}×{self.root.winfo_height()}")
        lines.append(f"状态: {'空闲' if not self._converting else '转换中'}")
        lines.append("")

        lines.append("【图片状态】")
        if self.original_image:
            lines.append(f"原图: {self.original_image.size[0]}×{self.original_image.size[1]} {self.original_image.mode}")
        else:
            lines.append("原图: 无")
        if self.result_image:
            lines.append(f"结果: {self.result_image.size[0]}×{self.result_image.size[1]} {self.result_image.mode}")
        else:
            lines.append("结果: 无")
        lines.append(f"网格: {self.grid_w}×{self.grid_h}")
        lines.append("")

        lines.append("【转换】")
        lines.append(f"块: {self.block_var.get()}")
        lines.append(f"颜色: {self.color_var.get()}")
        lines.append(f"色盘: {self.palette_var.get()}")
        lines.append(f"抖动: {self.settings.get('dither_method', 'NONE')}")
        lines.append(f"转换中: {self._converting}")
        lines.append(f"待处理: {self._pending_convert}")
        lines.append(f"未保存: {self.dirty}")
        lines.append("")

        lines.append("【批量】")
        lines.append(f"批量模式: {self.is_batch_mode}")
        if self.is_batch_mode:
            lines.append(f"索引: {self.batch_index+1}/{len(self.batch_images)}")
        lines.append("")

        lines.append("【编辑器】")
        if self.edit_window is not None and self.edit_window.winfo_exists():
            lines.append(f"网格: {self.edit_grid_w}×{self.edit_grid_h}")
            if hasattr(self, "tool_var"):
                lines.append(f"工具: {self.tool_var.get()}")
            lines.append(f"颜色: {self._grid_to_hex(self.current_color)}")
            lines.append(f"画笔: {self.settings.get('brush_size', 1)}")
            lines.append(f"选区: {len(self.edit_selection)} 格")
            lines.append(f"剪贴板: {len(self.edit_clipboard)} 格")
            lines.append(f"undo: {len(self.undo_stack)}/{self.undo_stack.maxlen}")
            lines.append(f"redo: {len(self.redo_stack)}/{self.redo_stack.maxlen}")
            lines.append(f"未应用: {self._editor_dirty}")
            lines.append(f"网格线: {'开' if self.show_grid_lines else '关'}")
        else:
            lines.append("编辑器未打开")
        lines.append("")

        lines.append("【鼠标位置】")
        if self._mouse_main_canvas is not None:
            lines.append(f"主画布: ({self._mouse_main_canvas[0]}, {self._mouse_main_canvas[1]})")
        else:
            lines.append("主画布: -")
        if self._mouse_editor_grid is not None:
            gx, gy = self._mouse_editor_grid
            if hasattr(self, "edit_grid") and 0 <= gy < len(self.edit_grid) and 0 <= gx < len(self.edit_grid[gy]):
                col = self.edit_grid[gy][gx]
                lines.append(f"编辑器: ({gx},{gy})  #{col[0]:02x}{col[1]:02x}{col[2]:02x}")
            else:
                lines.append(f"编辑器: ({gx},{gy})")
        else:
            lines.append("编辑器: -")
        lines.append("")

        lines.append("【其他】")
        lines.append(f"调色板缓存: {len(_palette_cache)} 条")
        lines.append(f"最近打开: {len(self.recent_files)} 条")
        lines.append(f"对比视图: {'打开' if self.compare_window and self.compare_window.winfo_exists() else '关闭'}")
        lines.append(f"首选项: {'打开' if self._pref_window and self._pref_window.winfo_exists() else '关闭'}")
        lines.append(f"日志级别: {self.dev.get('log_level', 'INFO')}")
        lines.append(f"调色板缓存开关: {'开' if self.dev.get('palette_cache_enabled', True) else '关'}")
        return "\n".join(lines)

    # ============================ 首选项 ============================
    def _make_scrollable_frame(self, parent):
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            canvas.itemconfig(inner_id, width=event.width)

        def on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        inner.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        return inner

    def _color_button(self, parent, initial, title):
        holder = [initial]
        btn = tk.Button(parent, width=4, bg=initial)
        btn.pack(side=tk.LEFT)
        def pick():
            c = self._pick_color(color=holder[0], title=title)
            if c and c[1]:
                holder[0] = c[1]
                btn.config(bg=c[1])
        tk.Button(parent, text="选择...", command=pick).pack(side=tk.LEFT, padx=5)
        return holder

    def _pref_hint(self, parent, text, row, colspan=2, indent=30):
        tk.Label(parent, text=text, fg="#888", font=("Arial", 8),
                 anchor="w", justify="left", wraplength=560).grid(
            row=row, column=0, columnspan=colspan, sticky="w",
            padx=(indent, 10), pady=(0, 6))
        return row + 1

    def _pref_hint_pack(self, parent, text, indent=24):
        tk.Label(parent, text=text, fg="#888", font=("Arial", 8),
                 anchor="w", justify="left", wraplength=560).pack(
            anchor="w", padx=(indent, 10), pady=(0, 6))

    def open_preferences(self):
        if self._pref_window is not None and self._pref_window.winfo_exists():
            self._pref_window.lift()
            return

        win = tk.Toplevel(self.root)
        self._pref_window = win
        win.title("首选项")
        win.geometry("720x640")
        win.transient(self.root)
        win.grab_set()
        win.resizable(False, False)

        nb = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ---------- 常规 ----------
        page1 = ttk.Frame(nb)
        nb.add(page1, text="常规")

        lf_title = ttk.LabelFrame(page1, text="系统标题栏")
        lf_title.pack(fill=tk.X, padx=10, pady=(10, 5))

        v_show_kaomoji = tk.BooleanVar(value=self.settings.get("show_kaomoji", True))
        v_title_suffix = tk.StringVar(value=self.settings.get("title_custom_suffix", ""))

        r = 0
        tk.Checkbutton(lf_title, text="在标题栏显示颜文字",
                       variable=v_show_kaomoji).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=10, pady=(6, 0)); r += 1
        r = self._pref_hint(lf_title, "勾选后在标题栏显示一个随机颜文字，与版本号一起展示", r)

        tk.Label(lf_title, text="自定义后缀:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Entry(lf_title, textvariable=v_title_suffix, width=30).grid(
            row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_title, "显示在标题栏末尾的额外文字，如「开发版」「测试」；留空则不显示", r)

        r = self._pref_hint(lf_title, "注意：系统标题栏的文字颜色由操作系统控制，无法在此修改", r)

        lf_win = ttk.LabelFrame(page1, text="窗口与缩放")
        lf_win.pack(fill=tk.X, padx=10, pady=5)

        v_win_w = tk.IntVar(value=self.settings.get("window_width", 885))
        v_win_h = tk.IntVar(value=self.settings.get("window_height", 636))
        v_zoom_step = tk.DoubleVar(value=self.settings.get("wheel_zoom_step", 0.1))

        r = 0
        tk.Label(lf_win, text="启动窗口尺寸:").grid(row=r, column=0, sticky="w", padx=10, pady=(6, 0))
        f_wh = tk.Frame(lf_win); f_wh.grid(row=r, column=1, sticky="w", pady=(6, 0))
        tk.Spinbox(f_wh, from_=640, to=3840, textvariable=v_win_w, width=6).pack(side=tk.LEFT)
        tk.Label(f_wh, text=" x ").pack(side=tk.LEFT)
        tk.Spinbox(f_wh, from_=480, to=2160, textvariable=v_win_h, width=6).pack(side=tk.LEFT)
        tk.Label(f_wh, text=" 像素").pack(side=tk.LEFT, padx=(5, 0)); r += 1
        r = self._pref_hint(lf_win, "程序启动时主窗口的初始宽高，单位为像素；下次启动生效", r)

        tk.Label(lf_win, text="鼠标滚轮缩放步长:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_win, from_=0.01, to=0.5, increment=0.01,
                   textvariable=v_zoom_step, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_win, "滚轮每滚一格的缩放百分比；0.1 表示每次缩放 10%，立即生效", r)

        # ---------- 转换 ----------
        page2 = ttk.Frame(nb)
        nb.add(page2, text="转换")
        v_def_block = tk.IntVar(value=self.settings.get("default_block", 12))
        v_def_colors = tk.IntVar(value=self.settings.get("default_colors", 16))
        v_def_palette = tk.StringVar(value=self.settings.get("default_palette", "自动"))
        v_remember = tk.BooleanVar(value=self.settings.get("remember_last_params", True))
        v_quant = tk.StringVar(value=self.settings.get("quantize_method", "MEDIANCUT"))
        v_dither_display = tk.StringVar(
            value=DITHER_DISPLAY.get(self.settings.get("dither_method", "NONE"), "无"))

        r = 0
        tk.Label(page2, text="默认块大小:").grid(row=r, column=0, sticky="w", padx=10, pady=(8, 0))
        tk.Spinbox(page2, from_=2, to=40, textvariable=v_def_block, width=8).grid(row=r, column=1, sticky="w", pady=(8, 0)); r += 1
        r = self._pref_hint(page2, "每次转换时使用的块大小默认值；块越大像素越大、细节越少", r)

        tk.Label(page2, text="默认颜色数:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(page2, from_=2, to=256, textvariable=v_def_colors, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(page2, "色盘为「自动」时使用的颜色数量；越少越像复古游戏", r)

        tk.Label(page2, text="默认色盘:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        ttk.Combobox(page2, textvariable=v_def_palette, values=list(PALETTES.keys()),
                     state="readonly", width=22).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(page2, "选择预设的复古色盘；选「自动」则按颜色数自动量化", r)

        tk.Checkbutton(page2, text="记住上次使用的参数", variable=v_remember).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 0)); r += 1
        r = self._pref_hint(page2, "勾选后每次启动恢复上次使用的块大小/颜色数/色盘；取消则每次都用默认值", r)

        tk.Label(page2, text="量化方法:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        ttk.Combobox(page2, textvariable=v_quant,
                     values=["MEDIANCUT", "MAXCOVERAGE", "FASTOCTREE"],
                     state="readonly", width=22).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(page2, "色盘为「自动」时使用的调色板生成算法；MEDIANCUT 最常用", r)

        tk.Label(page2, text="抖动方式:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        ttk.Combobox(page2, textvariable=v_dither_display,
                     values=list(DITHER_DISPLAY.values()),
                     state="readonly", width=22).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(page2, "抖动通过混色模拟更多颜色。低色数时明显改善观感，256 色时几乎无差别", r)

        # ---------- 编辑器 ----------
        page3 = ttk.Frame(nb)
        nb.add(page3, text="编辑器")
        v_undo = tk.IntVar(value=self.settings.get("undo_limit", 100))
        v_brush = tk.IntVar(value=self.settings.get("brush_size", 1))
        v_eraser = list(self.settings.get("eraser_color", [128, 128, 128]))
        v_show_grid = tk.BooleanVar(value=self.settings.get("default_show_grid", True))
        v_grid_color = [self.settings.get("grid_line_color", "#333333")]
        v_def_tool = tk.StringVar(value=self.settings.get("default_tool", "画笔"))

        r = 0
        tk.Label(page3, text="撤销步数上限:").grid(row=r, column=0, sticky="w", padx=10, pady=(8, 0))
        tk.Spinbox(page3, from_=10, to=500, textvariable=v_undo, width=8).grid(row=r, column=1, sticky="w", pady=(8, 0)); r += 1
        r = self._pref_hint(page3, "编辑器最多保留的撤销步数；步数越多占用内存越大", r)

        tk.Label(page3, text="画笔大小:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(page3, from_=1, to=8, textvariable=v_brush, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(page3, "画笔一笔覆盖的格子数；1 为单格，3 为 3×3 范围", r)

        tk.Label(page3, text="橡皮擦颜色:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        f = tk.Frame(page3); f.grid(row=r, column=1, sticky="w", pady=(4, 0))
        eraser_btn = tk.Button(f, width=4, bg=f"#{v_eraser[0]:02x}{v_eraser[1]:02x}{v_eraser[2]:02x}")
        eraser_btn.pack(side=tk.LEFT)
        def pick_eraser():
            c = self._pick_color(color=tuple(v_eraser), title="选择橡皮擦颜色")
            if c and c[0]:
                v_eraser[:] = [int(x) for x in c[0]]
                eraser_btn.config(bg=f"#{v_eraser[0]:02x}{v_eraser[1]:02x}{v_eraser[2]:02x}")
        tk.Button(f, text="选择...", command=pick_eraser).pack(side=tk.LEFT, padx=5); r += 1
        r = self._pref_hint(page3, "使用橡皮擦时填充的颜色，默认中灰；点击色块更换", r)

        tk.Checkbutton(page3, text="默认显示网格线", variable=v_show_grid).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 0)); r += 1
        r = self._pref_hint(page3, "打开编辑器时是否默认绘制格子边界线；编辑器内可随时切换", r)

        tk.Label(page3, text="网格线颜色:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        f = tk.Frame(page3); f.grid(row=r, column=1, sticky="w", pady=(4, 0))
        grid_btn = tk.Button(f, width=4, bg=v_grid_color[0])
        grid_btn.pack(side=tk.LEFT)
        def pick_grid():
            c = self._pick_color(color=v_grid_color[0], title="选择网格线颜色")
            if c and c[1]:
                v_grid_color[0] = c[1]
                grid_btn.config(bg=c[1])
        tk.Button(f, text="选择...", command=pick_grid).pack(side=tk.LEFT, padx=5); r += 1
        r = self._pref_hint(page3, "编辑器网格线的颜色；浅色系图片建议用深色网格线", r)

        tk.Label(page3, text="默认工具:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        ttk.Combobox(page3, textvariable=v_def_tool,
                     values=["画笔", "橡皮", "框选", "填充", "吸管"],
                     state="readonly", width=22).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(page3, "打开编辑器时默认选中的工具", r)

        # ---------- 保存 ----------
        page4 = ttk.Frame(nb)
        nb.add(page4, text="保存")
        v_fmt = tk.StringVar(value=self.settings.get("default_save_format", "PNG"))
        v_save_dir = tk.StringVar(value=self.settings.get("fixed_save_dir", ""))

        r = 0
        tk.Label(page4, text="默认保存格式:").grid(row=r, column=0, sticky="w", padx=10, pady=(8, 0))
        ttk.Combobox(page4, textvariable=v_fmt, values=["PNG", "JPG", "BMP"],
                     state="readonly", width=22).grid(row=r, column=1, sticky="w", pady=(8, 0)); r += 1
        r = self._pref_hint(page4, "保存对话框默认选中的格式；像素画建议用 PNG 以保留锐利边缘", r)

        tk.Label(page4, text="固定保存目录:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        f = tk.Frame(page4); f.grid(row=r, column=1, sticky="w", pady=(4, 0))
        tk.Entry(f, textvariable=v_save_dir, width=30).pack(side=tk.LEFT)
        def pick_dir():
            d = filedialog.askdirectory(initialdir=v_save_dir.get() or None, parent=win)
            if d:
                v_save_dir.set(d)
        tk.Button(f, text="浏览...", command=pick_dir).pack(side=tk.LEFT, padx=5); r += 1
        r = self._pref_hint(page4, "每次保存时打开的起始目录；留空则每次使用系统默认目录", r)

        # ---------- 高级 ----------
        page5 = ttk.Frame(nb)
        nb.add(page5, text="高级")
        v_rs_orig = tk.StringVar(value=self.settings.get("resample_original", "BILINEAR"))
        v_rs_res = tk.StringVar(value=self.settings.get("resample_result", "NEAREST"))

        r = 0
        tk.Label(page5, text="原图预览重采样:").grid(row=r, column=0, sticky="w", padx=10, pady=(8, 0))
        ttk.Combobox(page5, textvariable=v_rs_orig,
                     values=["NEAREST", "BILINEAR", "BICUBIC", "LANCZOS"],
                     state="readonly", width=22).grid(row=r, column=1, sticky="w", pady=(8, 0)); r += 1
        r = self._pref_hint(page5, "主窗口中「原图」预览的缩放算法；BILINEAR 兼顾速度和平滑", r)

        tk.Label(page5, text="像素画预览重采样:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        ttk.Combobox(page5, textvariable=v_rs_res,
                     values=["NEAREST", "BILINEAR", "BICUBIC", "LANCZOS"],
                     state="readonly", width=22).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(page5, "主窗口中「像素画」预览的缩放算法；NEAREST 保持硬边缘不糊", r)

        # ---------- 开发者 ----------
        page6 = ttk.Frame(nb)
        nb.add(page6, text="开发者")

        dev_nb = ttk.Notebook(page6)
        dev_nb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ===== 常量 =====
        const_page = ttk.Frame(dev_nb)
        dev_nb.add(const_page, text="常量")
        ci = self._make_scrollable_frame(const_page)
        lf_const = ttk.LabelFrame(ci, text="常量（改动需重启）")
        lf_const.pack(fill=tk.X, padx=10, pady=(10, 5))

        v_version_text = tk.StringVar(value=self.dev.get("version_text", VERSION))
        v_kaomoji_csv = tk.StringVar(value=self.dev.get("kaomoji_csv", ""))
        v_presets_json = tk.StringVar(value=self.dev.get("presets_json", "{}"))
        v_recent_max = tk.IntVar(value=int(self.dev.get("recent_max", 5)))
        v_palette_cache = tk.BooleanVar(value=bool(self.dev.get("palette_cache_enabled", True)))
        v_log_path = tk.StringVar(value=self.dev.get("log_file_path", "pixelcraft.log"))
        v_log_max = tk.IntVar(value=int(self.dev.get("log_max_lines", 5000)))

        r = 0
        tk.Label(lf_const, text="版本文字:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Entry(lf_const, textvariable=v_version_text, width=30).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_const, "显示在标题栏、检查更新、关于中的版本号；修改后需重启", r)

        tk.Label(lf_const, text="颜文字列表（逗号分隔）:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Entry(lf_const, textvariable=v_kaomoji_csv, width=40).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_const, "每次启动从这些颜文字中随机取一个，用英文逗号分隔；修改后需重启", r)

        tk.Label(lf_const, text="预设尺寸（JSON）:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Entry(lf_const, textvariable=v_presets_json, width=40).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_const, '格式 {"名称":[宽,高],...}；出现在编辑菜单和下拉框中；修改后需重启', r)

        tk.Label(lf_const, text="最近打开上限:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_const, from_=1, to=30, textvariable=v_recent_max, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_const, "「最近打开」菜单保留的条目数量上限；修改后需重启", r)

        tk.Checkbutton(lf_const, text="启用调色板缓存（关闭后每次转换重新构建）",
                       variable=v_palette_cache).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 0)); r += 1
        r = self._pref_hint(lf_const, "开启后相同色盘只构建一次，转换更快；关闭用于调试或排查缓存问题", r)

        tk.Label(lf_const, text="日志文件路径:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Entry(lf_const, textvariable=v_log_path, width=30).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_const, "开启日志写入文件时的保存路径；相对路径基于工作目录", r)

        tk.Label(lf_const, text="日志最大行数:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_const, from_=100, to=100000, textvariable=v_log_max, width=10).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_const, "日志文件超过此数时自动裁剪旧内容只保留尾部；防止无限增长", r)

        # ===== 数值范围 =====
        range_page = ttk.Frame(dev_nb)
        dev_nb.add(range_page, text="数值范围")
        ri = self._make_scrollable_frame(range_page)
        lf_range = ttk.LabelFrame(ri, text="数值范围（改动需重启）")
        lf_range.pack(fill=tk.X, padx=10, pady=(10, 5))

        v_block_min = tk.IntVar(value=int(self.dev.get("block_min", 2)))
        v_block_max = tk.IntVar(value=int(self.dev.get("block_max", 40)))
        v_colors_min = tk.IntVar(value=int(self.dev.get("colors_min", 2)))
        v_colors_max = tk.IntVar(value=int(self.dev.get("colors_max", 64)))
        v_preset_cap = tk.IntVar(value=int(self.dev.get("preset_new_block_cap", 40)))
        v_min_w = tk.IntVar(value=int(self.dev.get("min_window_width", 800)))
        v_min_h = tk.IntVar(value=int(self.dev.get("min_window_height", 600)))
        v_recent_trunc = tk.IntVar(value=int(self.dev.get("recent_menu_truncate", 40)))

        r = 0
        tk.Label(lf_range, text="块最小:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_range, from_=1, to=20, textvariable=v_block_min, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_range, "主界面「块」滑块的下限，低于此值无法拖动；修改后需重启", r)

        tk.Label(lf_range, text="块最大:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_range, from_=4, to=200, textvariable=v_block_max, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_range, "主界面「块」滑块的上限；修改后需重启", r)

        tk.Label(lf_range, text="颜色最小:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_range, from_=2, to=32, textvariable=v_colors_min, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_range, "主界面「颜色」滑块的下限；修改后需重启", r)

        tk.Label(lf_range, text="颜色最大:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_range, from_=4, to=256, textvariable=v_colors_max, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_range, "主界面「颜色」滑块的上限；修改后需重启", r)

        tk.Label(lf_range, text="预设网格上限:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_range, from_=8, to=200, textvariable=v_preset_cap, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_range, "选择预设时自动计算的块大小上限，防止过大图块数太少；修改后需重启", r)

        tk.Label(lf_range, text="最小窗口宽:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_range, from_=400, to=1920, textvariable=v_min_w, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_range, "主窗口可拖拽的最小宽度；修改后需重启", r)

        tk.Label(lf_range, text="最小窗口高:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_range, from_=300, to=1200, textvariable=v_min_h, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_range, "主窗口可拖拽的最小高度；修改后需重启", r)

        tk.Label(lf_range, text="最近打开菜单截断长度:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_range, from_=8, to=200, textvariable=v_recent_trunc, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_range, "菜单中文件名超过此长度显示省略号；修改后需重启", r)

        # ===== 性能 =====
        perf_page = ttk.Frame(dev_nb)
        dev_nb.add(perf_page, text="性能")
        pi = self._make_scrollable_frame(perf_page)
        lf_perf = ttk.LabelFrame(pi, text="性能（立即生效）")
        lf_perf.pack(fill=tk.X, padx=10, pady=(10, 5))

        v_debounce = tk.IntVar(value=int(self.dev.get("convert_debounce_ms", 150)))
        v_batch_threads = tk.IntVar(value=int(self.dev.get("batch_threads", 4)))
        v_batch_poll = tk.IntVar(value=int(self.dev.get("batch_poll_ms", 200)))
        v_smooth_threshold = tk.IntVar(value=int(self.dev.get("smooth_resize_threshold", 2000)))

        r = 0
        tk.Label(lf_perf, text="转换去抖延迟 (ms):").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_perf, from_=0, to=2000, textvariable=v_debounce, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_perf, "参数变化后等待多久再开始转换；越大越省 CPU，但响应越慢", r)

        tk.Label(lf_perf, text="批量保存线程数:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_perf, from_=1, to=16, textvariable=v_batch_threads, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_perf, "批量保存时并行的图片数量；1 为串行，数字越大越快但越耗 CPU", r)

        tk.Label(lf_perf, text="批量保存轮询 (ms):").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_perf, from_=50, to=2000, textvariable=v_batch_poll, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_perf, "进度条刷新的间隔；越小越流畅但占用事件循环越多", r)

        tk.Label(lf_perf, text="平滑缩放阈值 (像素):").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_perf, from_=0, to=100000, textvariable=v_smooth_threshold, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_perf, "原图宽或高超过此值时强制改用 BILINEAR 缩放；0 表示不限制", r)

        # ===== 算法 =====
        algo_page = ttk.Frame(dev_nb)
        dev_nb.add(algo_page, text="算法")
        ai = self._make_scrollable_frame(algo_page)
        lf_algo = ttk.LabelFrame(ai, text="算法参数（立即生效）")
        lf_algo.pack(fill=tk.X, padx=10, pady=(10, 5))

        v_bayer = tk.DoubleVar(value=float(self.dev.get("bayer_spread_multiplier", 1.0)))
        v_atkinson = tk.DoubleVar(value=float(self.dev.get("atkinson_error_scale", 1.0)))
        v_weighted = tk.BooleanVar(value=bool(self.dev.get("nearest_use_weighted", False)))
        v_wr = tk.DoubleVar(value=float(self.dev.get("nearest_weight_r", 2.0)))
        v_wg = tk.DoubleVar(value=float(self.dev.get("nearest_weight_g", 4.0)))
        v_wb = tk.DoubleVar(value=float(self.dev.get("nearest_weight_b", 3.0)))
        v_exif = tk.BooleanVar(value=bool(self.dev.get("exif_transpose", True)))

        r = 0
        tk.Label(lf_algo, text="Bayer 扩散系数:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_algo, from_=0.1, to=5.0, increment=0.1, textvariable=v_bayer, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_algo, "Bayer 抖动时的误差扩散强度；1 为标准，越大越花，越小越平", r)

        tk.Label(lf_algo, text="Atkinson 误差系数:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_algo, from_=0.1, to=5.0, increment=0.1, textvariable=v_atkinson, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_algo, "Atkinson 抖动的误差扩散强度；调大偏黑白，调小接近 FS", r)

        tk.Checkbutton(lf_algo, text="最近色使用人眼感知加权", variable=v_weighted).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 0)); r += 1
        r = self._pref_hint(lf_algo, "开启后按人眼对 RGB 敏感度加权匹配，绿色系更自然但更慢", r)

        tk.Label(lf_algo, text="R 权重:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_algo, from_=0.1, to=10.0, increment=0.1, textvariable=v_wr, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_algo, "红色分量的匹配权重；越大越容易被忽略", r)

        tk.Label(lf_algo, text="G 权重:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_algo, from_=0.1, to=10.0, increment=0.1, textvariable=v_wg, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_algo, "绿色分量的匹配权重；人眼对绿色最敏感，默认最高", r)

        tk.Label(lf_algo, text="B 权重:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_algo, from_=0.1, to=10.0, increment=0.1, textvariable=v_wb, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_algo, "蓝色分量的匹配权重；人眼对蓝色敏感度最低，通常与 R 相近", r)

        tk.Checkbutton(lf_algo, text="自动应用 EXIF 方向", variable=v_exif).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 0)); r += 1
        r = self._pref_hint(lf_algo, "手机照片常带方向元数据；开启后加载时自动旋转到正方向", r)

        # ===== 保存 =====
        save_page = ttk.Frame(dev_nb)
        dev_nb.add(save_page, text="保存")
        si = self._make_scrollable_frame(save_page)
        lf_save = ttk.LabelFrame(si, text="保存参数（立即生效）")
        lf_save.pack(fill=tk.X, padx=10, pady=(10, 5))

        v_jpg_q = tk.IntVar(value=int(self.dev.get("jpg_quality", 95)))
        v_png_cl = tk.IntVar(value=int(self.dev.get("png_compress_level", 6)))
        v_png_opt = tk.BooleanVar(value=bool(self.dev.get("png_optimize", False)))

        r = 0
        tk.Label(lf_save, text="JPG 质量 (1-100):").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_save, from_=1, to=100, textvariable=v_jpg_q, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_save, "保存 JPG 时的压缩质量；100 几乎无损但文件大，60-80 常用", r)

        tk.Label(lf_save, text="PNG 压缩级别 (0-9):").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_save, from_=0, to=9, textvariable=v_png_cl, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_save, "0 不压缩最快、文件最大；9 压缩最强最慢；不影响像素质量", r)

        tk.Checkbutton(lf_save, text="PNG 启用 optimize（更慢但更小）", variable=v_png_opt).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 0)); r += 1
        r = self._pref_hint(lf_save, "开启后尝试最优压缩参数组合；大图可能耗时明显增加", r)

        # ===== 缩放 =====
        zoom_page = ttk.Frame(dev_nb)
        dev_nb.add(zoom_page, text="缩放")
        zi = self._make_scrollable_frame(zoom_page)
        lf_zoom = ttk.LabelFrame(zi, text="缩放（立即生效）")
        lf_zoom.pack(fill=tk.X, padx=10, pady=(10, 5))

        v_zoom_in = tk.DoubleVar(value=float(self.dev.get("zoom_in_factor", 1.15)))
        v_zoom_out = tk.DoubleVar(value=float(self.dev.get("zoom_out_factor", 0.85)))
        v_zoom_min = tk.DoubleVar(value=float(self.dev.get("zoom_min", 0.1)))
        v_zoom_max = tk.DoubleVar(value=float(self.dev.get("zoom_max", 10.0)))

        r = 0
        tk.Label(lf_zoom, text="放大系数:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_zoom, from_=1.01, to=3.0, increment=0.01, textvariable=v_zoom_in, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_zoom, "点击「放大」按钮时缩放倍数；1.15 表示放大到 115%", r)

        tk.Label(lf_zoom, text="缩小系数:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_zoom, from_=0.1, to=0.99, increment=0.01, textvariable=v_zoom_out, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_zoom, "点击「缩小」按钮时缩放倍数；0.85 表示缩小到 85%", r)

        tk.Label(lf_zoom, text="缩放下限:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_zoom, from_=0.01, to=1.0, increment=0.01, textvariable=v_zoom_min, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_zoom, "鼠标滚轮/按钮缩放能达到的最小倍数，防止缩太小看不到", r)

        tk.Label(lf_zoom, text="缩放上限:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_zoom, from_=1.0, to=50.0, increment=0.5, textvariable=v_zoom_max, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_zoom, "缩放能达到的最大倍数，过大可能导致内存占用飙升", r)

        # ===== 外观 =====
        look_page = ttk.Frame(dev_nb)
        dev_nb.add(look_page, text="外观")
        li = self._make_scrollable_frame(look_page)
        lf_look = ttk.LabelFrame(li, text="外观（立即生效）")
        lf_look.pack(fill=tk.X, padx=10, pady=(10, 5))

        v_font_family = tk.StringVar(value=self.dev.get("font_family", ""))
        v_font_size = tk.IntVar(value=int(self.dev.get("font_size", 0) or 0))

        r = 0
        tk.Label(lf_look, text="主画布背景色:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        f = tk.Frame(lf_look); f.grid(row=r, column=1, sticky="w", pady=(4, 0))
        v_canvas_bg = self._color_button(f, self.dev.get("canvas_bg", "#1e1e1e"), "主画布背景色")
        r += 1
        r = self._pref_hint(lf_look, "原图/像素画两侧画布的底色；深色能突出像素画本身", r)

        tk.Label(lf_look, text="编辑器画布背景色:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        f = tk.Frame(lf_look); f.grid(row=r, column=1, sticky="w", pady=(4, 0))
        v_editor_bg = self._color_button(f, self.dev.get("editor_canvas_bg", "#1e1e1e"), "编辑器画布背景色")
        r += 1
        r = self._pref_hint(lf_look, "像素画编辑器画布的底色；网格线以外区域", r)

        tk.Label(lf_look, text="状态栏文字色:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        f = tk.Frame(lf_look); f.grid(row=r, column=1, sticky="w", pady=(4, 0))
        v_status_fg = self._color_button(f, self.dev.get("status_fg", "blue"), "状态栏文字色")
        r += 1
        r = self._pref_hint(lf_look, "主窗口底部状态栏普通提示文字的颜色", r)

        tk.Label(lf_look, text="状态栏成功色:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        f = tk.Frame(lf_look); f.grid(row=r, column=1, sticky="w", pady=(4, 0))
        v_status_ok = self._color_button(f, self.dev.get("status_success_fg", "green"), "状态栏成功色")
        r += 1
        r = self._pref_hint(lf_look, "保存/导出成功时状态栏文字的颜色", r)

        tk.Label(lf_look, text="状态栏错误色:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        f = tk.Frame(lf_look); f.grid(row=r, column=1, sticky="w", pady=(4, 0))
        v_status_err = self._color_button(f, self.dev.get("status_error_fg", "red"), "状态栏错误色")
        r += 1
        r = self._pref_hint(lf_look, "转换/保存失败时状态栏文字的颜色", r)

        tk.Label(lf_look, text="编辑器选中框颜色:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        f = tk.Frame(lf_look); f.grid(row=r, column=1, sticky="w", pady=(4, 0))
        v_sel_color = self._color_button(f, self.dev.get("editor_selection_color", "#00FF00"), "编辑器选中框颜色")
        r += 1
        r = self._pref_hint(lf_look, "框选工具产生的选区高亮边框颜色", r)

        tk.Label(lf_look, text="编辑器拖拽框颜色:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        f = tk.Frame(lf_look); f.grid(row=r, column=1, sticky="w", pady=(4, 0))
        v_drag_color = self._color_button(f, self.dev.get("editor_drag_color", "#00FF00"), "编辑器拖拽框颜色")
        r += 1
        r = self._pref_hint(lf_look, "框选工具拖拽过程中虚线预览框的颜色", r)

        tk.Label(lf_look, text="界面字体（留空用默认）:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Entry(lf_look, textvariable=v_font_family, width=20).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_look, "全局字体名称如 Microsoft YaHei、SimHei；留空使用系统默认；需重启", r)

        tk.Label(lf_look, text="基础字号（0 用默认）:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_look, from_=0, to=40, textvariable=v_font_size, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_look, "全局字体基础大小，单位 pt；0 表示不覆盖系统默认；需重启", r)

        # ===== 日志 =====
        log_page = ttk.Frame(dev_nb)
        dev_nb.add(log_page, text="日志")
        logi = self._make_scrollable_frame(log_page)
        lf_log = ttk.LabelFrame(logi, text="日志（立即生效）")
        lf_log.pack(fill=tk.X, padx=10, pady=(10, 5))

        v_log_level = tk.StringVar(value=self.dev.get("log_level", "INFO"))
        v_log_console = tk.BooleanVar(value=bool(self.dev.get("log_to_console", False)))
        v_log_file = tk.BooleanVar(value=bool(self.dev.get("log_to_file", False)))
        v_watch_refresh = tk.IntVar(value=int(self.dev.get("watch_refresh_ms", 250)))

        r = 0
        tk.Label(lf_log, text="日志级别:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        ttk.Combobox(lf_log, textvariable=v_log_level,
                     values=list(LOG_LEVEL_NAMES.keys()),
                     state="readonly", width=15).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_log, "低于此级别的日志不记录；DEBUG 最详细、NONE 关闭日志", r)

        tk.Checkbutton(lf_log, text="输出到控制台", variable=v_log_console).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 0)); r += 1
        r = self._pref_hint(lf_log, "把日志打印到 stderr；从终端启动时可看到实时输出", r)

        tk.Checkbutton(lf_log, text="输出到文件", variable=v_log_file).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 0)); r += 1
        r = self._pref_hint(lf_log, "把日志追加到「常量」页指定的文件路径；超过最大行数自动裁剪", r)

        tk.Label(lf_log, text="监视窗口刷新间隔 (ms):").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_log, from_=100, to=2000, increment=50, textvariable=v_watch_refresh, width=8).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_log, "F12 监视窗口自动刷新的时间间隔；越大越省 CPU", r)

        # ===== 调试 =====
        debug_page = ttk.Frame(dev_nb)
        dev_nb.add(debug_page, text="调试")
        di = self._make_scrollable_frame(debug_page)
        lf_debug = ttk.LabelFrame(di, text="调试开关（立即生效）")
        lf_debug.pack(fill=tk.X, padx=10, pady=(10, 5))

        v_show_time = tk.BooleanVar(value=bool(self.dev.get("show_convert_time", True)))
        v_debug_console = tk.BooleanVar(value=bool(self.dev.get("debug_console", False)))
        v_grid_threshold = tk.IntVar(value=int(self.dev.get("editor_grid_render_threshold", 0)))
        v_show_coords = tk.BooleanVar(value=bool(self.dev.get("show_hover_coords", True)))

        r = 0
        tk.Checkbutton(lf_debug, text="状态栏显示转换耗时", variable=v_show_time).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 0)); r += 1
        r = self._pref_hint(lf_debug, "每次转换完成后在主窗口状态栏显示耗时毫秒数", r)

        tk.Checkbutton(lf_debug, text="控制台输出调试信息", variable=v_debug_console).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 0)); r += 1
        r = self._pref_hint(lf_debug, "把调试日志打印到控制台；和「日志-输出到控制台」效果类似", r)

        tk.Label(lf_debug, text="编辑器网格渲染阈值（0=不限制）:").grid(row=r, column=0, sticky="w", padx=10, pady=(4, 0))
        tk.Spinbox(lf_debug, from_=0, to=1000000, textvariable=v_grid_threshold, width=10).grid(row=r, column=1, sticky="w", pady=(4, 0)); r += 1
        r = self._pref_hint(lf_debug, "编辑器格子总数超过此值时自动关闭网格线以加速绘制；0 表示从不关闭", r)

        tk.Checkbutton(lf_debug, text="显示编辑器坐标悬停", variable=v_show_coords).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 0)); r += 1
        r = self._pref_hint(lf_debug, "鼠标在编辑器上移动时右上角显示当前格坐标和颜色", r)

        # ===== 实验 =====
        exp_page = ttk.Frame(dev_nb)
        dev_nb.add(exp_page, text="实验")
        ei = self._make_scrollable_frame(exp_page)
        lf_exp = ttk.LabelFrame(ei, text="实验性功能（立即生效）")
        lf_exp.pack(fill=tk.X, padx=10, pady=(10, 5))

        v_continuous = tk.BooleanVar(value=bool(self.dev.get("continuous_drag_draw", True)))
        v_editor_zoom = tk.BooleanVar(value=bool(self.dev.get("editor_mousewheel_zoom", False)))

        f1 = tk.Frame(lf_exp); f1.pack(fill=tk.X, padx=10, pady=(4, 0))
        tk.Checkbutton(f1, text="画笔连续拖拽绘制", variable=v_continuous).pack(anchor="w")
        self._pref_hint_pack(f1, "开启后按住鼠标拖动时经过的像素块都会被修改；关闭后只在按下位置修改一次")

        f2 = tk.Frame(lf_exp); f2.pack(fill=tk.X, padx=10, pady=(0, 0))
        tk.Checkbutton(f2, text="编辑器滚轮缩放（预留开关，当前未实现）", variable=v_editor_zoom).pack(anchor="w")
        self._pref_hint_pack(f2, "预留给后续版本使用的编辑器画布缩放功能，当前版本不会生效")

        f3 = tk.Frame(lf_exp); f3.pack(fill=tk.X, padx=10, pady=(0, 6))
        self._pref_hint_pack(f3, "实验性功能可能不稳定，请谨慎开启；出问题时关闭即可恢复")

        # ===== 工具 =====
        tool_page = ttk.Frame(dev_nb)
        dev_nb.add(tool_page, text="工具")
        ti = self._make_scrollable_frame(tool_page)
        lf_tool = ttk.LabelFrame(ti, text="调试与测试工具（不是设置项，点击即执行）")
        lf_tool.pack(fill=tk.X, padx=10, pady=(10, 5))

        self._pref_hint_pack(lf_tool, "以下按钮用于开发者调试，不属于设置项；点击后会立即执行对应操作", indent=10)

        tool_btns = tk.Frame(lf_tool); tool_btns.pack(fill=tk.X, padx=10, pady=8)
        tk.Button(tool_btns, text="生成棋盘测试图", command=lambda: self._dev_generate_test("checker"), width=16).pack(side=tk.LEFT, padx=(0, 5), pady=2)
        tk.Button(tool_btns, text="生成渐变测试图", command=lambda: self._dev_generate_test("gradient"), width=16).pack(side=tk.LEFT, padx=(0, 5), pady=2)
        tk.Button(tool_btns, text="生成噪点测试图", command=lambda: self._dev_generate_test("noise"), width=16).pack(side=tk.LEFT, padx=(0, 5), pady=2)
        tk.Button(tool_btns, text="生成对称测试图", command=lambda: self._dev_generate_test("symmetric"), width=16).pack(side=tk.LEFT, pady=2)

        tool_btns2 = tk.Frame(lf_tool); tool_btns2.pack(fill=tk.X, padx=10, pady=8)
        tk.Button(tool_btns2, text="性能基准", command=self._dev_benchmark, width=16).pack(side=tk.LEFT, padx=(0, 5), pady=2)
        tk.Button(tool_btns2, text="显示环境信息", command=self._dev_env_info, width=16).pack(side=tk.LEFT, padx=(0, 5), pady=2)
        tk.Button(tool_btns2, text="打开监视窗口", command=self.toggle_watch, width=16).pack(side=tk.LEFT, padx=(0, 5), pady=2)
        tk.Button(tool_btns2, text="测试异常处理", command=self._dev_test_error, width=16, bg="#ff9800", fg="white").pack(side=tk.LEFT, pady=2)

        # ===== 维护 =====
        maint_page = ttk.Frame(dev_nb)
        dev_nb.add(maint_page, text="维护")
        mi = self._make_scrollable_frame(maint_page)
        lf_maint = ttk.LabelFrame(mi, text="配置维护（不是设置项，点击即执行）")
        lf_maint.pack(fill=tk.X, padx=10, pady=(10, 5))

        self._pref_hint_pack(lf_maint, "以下按钮操作整个配置文件，请谨慎使用", indent=10)

        maint_btns = tk.Frame(lf_maint); maint_btns.pack(fill=tk.X, padx=10, pady=8)
        tk.Button(maint_btns, text="导出配置", command=self._dev_export_config, width=12).pack(side=tk.LEFT, padx=(0, 5), pady=2)
        tk.Button(maint_btns, text="导入配置", command=self._dev_import_config, width=12).pack(side=tk.LEFT, padx=(0, 5), pady=2)
        tk.Button(maint_btns, text="清空调色板缓存", command=self._dev_clear_palette_cache, width=14).pack(side=tk.LEFT, padx=(0, 5), pady=2)
        tk.Button(maint_btns, text="重置所有配置", command=self._dev_reset_config, width=14, bg="#d9534f", fg="white").pack(side=tk.LEFT, pady=2)

        # ---------- 底部按钮 ----------
        btns = tk.Frame(win)
        btns.pack(fill=tk.X, padx=10, pady=(0, 10))

        def restore_defaults():
            v_show_kaomoji.set(DEFAULT_SETTINGS["show_kaomoji"])
            v_title_suffix.set(DEFAULT_SETTINGS["title_custom_suffix"])
            v_win_w.set(DEFAULT_SETTINGS["window_width"])
            v_win_h.set(DEFAULT_SETTINGS["window_height"])
            v_zoom_step.set(DEFAULT_SETTINGS["wheel_zoom_step"])
            v_def_block.set(DEFAULT_SETTINGS["default_block"])
            v_def_colors.set(DEFAULT_SETTINGS["default_colors"])
            v_def_palette.set(DEFAULT_SETTINGS["default_palette"])
            v_remember.set(DEFAULT_SETTINGS["remember_last_params"])
            v_quant.set(DEFAULT_SETTINGS["quantize_method"])
            v_dither_display.set(DITHER_DISPLAY[DEFAULT_SETTINGS["dither_method"]])
            v_undo.set(DEFAULT_SETTINGS["undo_limit"])
            v_brush.set(DEFAULT_SETTINGS["brush_size"])
            v_eraser[:] = list(DEFAULT_SETTINGS["eraser_color"])
            eraser_btn.config(bg=f"#{v_eraser[0]:02x}{v_eraser[1]:02x}{v_eraser[2]:02x}")
            v_show_grid.set(DEFAULT_SETTINGS["default_show_grid"])
            v_grid_color[0] = DEFAULT_SETTINGS["grid_line_color"]
            grid_btn.config(bg=v_grid_color[0])
            v_def_tool.set(DEFAULT_SETTINGS["default_tool"])
            v_fmt.set(DEFAULT_SETTINGS["default_save_format"])
            v_save_dir.set(DEFAULT_SETTINGS["fixed_save_dir"])
            v_rs_orig.set(DEFAULT_SETTINGS["resample_original"])
            v_rs_res.set(DEFAULT_SETTINGS["resample_result"])
            v_version_text.set(DEV_DEFAULTS["version_text"])
            v_kaomoji_csv.set(DEV_DEFAULTS["kaomoji_csv"])
            v_presets_json.set(DEV_DEFAULTS["presets_json"])
            v_recent_max.set(DEV_DEFAULTS["recent_max"])
            v_palette_cache.set(DEV_DEFAULTS["palette_cache_enabled"])
            v_log_path.set(DEV_DEFAULTS["log_file_path"])
            v_log_max.set(DEV_DEFAULTS["log_max_lines"])
            v_block_min.set(DEV_DEFAULTS["block_min"])
            v_block_max.set(DEV_DEFAULTS["block_max"])
            v_colors_min.set(DEV_DEFAULTS["colors_min"])
            v_colors_max.set(DEV_DEFAULTS["colors_max"])
            v_preset_cap.set(DEV_DEFAULTS["preset_new_block_cap"])
            v_min_w.set(DEV_DEFAULTS["min_window_width"])
            v_min_h.set(DEV_DEFAULTS["min_window_height"])
            v_recent_trunc.set(DEV_DEFAULTS["recent_menu_truncate"])
            v_debounce.set(DEV_DEFAULTS["convert_debounce_ms"])
            v_batch_threads.set(DEV_DEFAULTS["batch_threads"])
            v_batch_poll.set(DEV_DEFAULTS["batch_poll_ms"])
            v_smooth_threshold.set(DEV_DEFAULTS["smooth_resize_threshold"])
            v_bayer.set(DEV_DEFAULTS["bayer_spread_multiplier"])
            v_atkinson.set(DEV_DEFAULTS["atkinson_error_scale"])
            v_weighted.set(DEV_DEFAULTS["nearest_use_weighted"])
            v_wr.set(DEV_DEFAULTS["nearest_weight_r"])
            v_wg.set(DEV_DEFAULTS["nearest_weight_g"])
            v_wb.set(DEV_DEFAULTS["nearest_weight_b"])
            v_exif.set(DEV_DEFAULTS["exif_transpose"])
            v_jpg_q.set(DEV_DEFAULTS["jpg_quality"])
            v_png_cl.set(DEV_DEFAULTS["png_compress_level"])
            v_png_opt.set(DEV_DEFAULTS["png_optimize"])
            v_zoom_in.set(DEV_DEFAULTS["zoom_in_factor"])
            v_zoom_out.set(DEV_DEFAULTS["zoom_out_factor"])
            v_zoom_min.set(DEV_DEFAULTS["zoom_min"])
            v_zoom_max.set(DEV_DEFAULTS["zoom_max"])
            v_canvas_bg[0] = DEV_DEFAULTS["canvas_bg"]
            v_editor_bg[0] = DEV_DEFAULTS["editor_canvas_bg"]
            v_status_fg[0] = DEV_DEFAULTS["status_fg"]
            v_status_ok[0] = DEV_DEFAULTS["status_success_fg"]
            v_status_err[0] = DEV_DEFAULTS["status_error_fg"]
            v_sel_color[0] = DEV_DEFAULTS["editor_selection_color"]
            v_drag_color[0] = DEV_DEFAULTS["editor_drag_color"]
            v_font_family.set(DEV_DEFAULTS["font_family"])
            v_font_size.set(DEV_DEFAULTS["font_size"])
            v_log_level.set(DEV_DEFAULTS["log_level"])
            v_log_console.set(DEV_DEFAULTS["log_to_console"])
            v_log_file.set(DEV_DEFAULTS["log_to_file"])
            v_watch_refresh.set(DEV_DEFAULTS["watch_refresh_ms"])
            v_show_time.set(DEV_DEFAULTS["show_convert_time"])
            v_debug_console.set(DEV_DEFAULTS["debug_console"])
            v_grid_threshold.set(DEV_DEFAULTS["editor_grid_render_threshold"])
            v_show_coords.set(DEV_DEFAULTS["show_hover_coords"])
            v_continuous.set(DEV_DEFAULTS["continuous_drag_draw"])
            v_editor_zoom.set(DEV_DEFAULTS["editor_mousewheel_zoom"])

        def on_ok():
            try:
                new_settings = {
                    "show_kaomoji": bool(v_show_kaomoji.get()),
                    "title_custom_suffix": v_title_suffix.get().strip(),
                    "window_width": int(v_win_w.get()),
                    "window_height": int(v_win_h.get()),
                    "wheel_zoom_step": float(v_zoom_step.get()),
                    "default_block": int(v_def_block.get()),
                    "default_colors": int(v_def_colors.get()),
                    "default_palette": v_def_palette.get(),
                    "remember_last_params": bool(v_remember.get()),
                    "quantize_method": v_quant.get(),
                    "dither_method": DITHER_DISPLAY_INV.get(v_dither_display.get(), "NONE"),
                    "undo_limit": int(v_undo.get()),
                    "brush_size": int(v_brush.get()),
                    "eraser_color": list(v_eraser),
                    "default_show_grid": bool(v_show_grid.get()),
                    "grid_line_color": v_grid_color[0],
                    "default_tool": v_def_tool.get(),
                    "default_save_format": v_fmt.get(),
                    "fixed_save_dir": v_save_dir.get().strip(),
                    "resample_original": v_rs_orig.get(),
                    "resample_result": v_rs_res.get(),
                }
                new_dev = dict(self.dev)
                new_dev.update({
                    "version_text": v_version_text.get().strip() or VERSION,
                    "kaomoji_csv": v_kaomoji_csv.get(),
                    "presets_json": v_presets_json.get(),
                    "recent_max": int(v_recent_max.get()),
                    "palette_cache_enabled": bool(v_palette_cache.get()),
                    "log_file_path": v_log_path.get().strip() or "pixelcraft.log",
                    "log_max_lines": int(v_log_max.get()),
                    "block_min": int(v_block_min.get()),
                    "block_max": int(v_block_max.get()),
                    "colors_min": int(v_colors_min.get()),
                    "colors_max": int(v_colors_max.get()),
                    "preset_new_block_cap": int(v_preset_cap.get()),
                    "min_window_width": int(v_min_w.get()),
                    "min_window_height": int(v_min_h.get()),
                    "recent_menu_truncate": int(v_recent_trunc.get()),
                    "convert_debounce_ms": int(v_debounce.get()),
                    "batch_threads": int(v_batch_threads.get()),
                    "batch_poll_ms": int(v_batch_poll.get()),
                    "smooth_resize_threshold": int(v_smooth_threshold.get()),
                    "bayer_spread_multiplier": float(v_bayer.get()),
                    "atkinson_error_scale": float(v_atkinson.get()),
                    "nearest_use_weighted": bool(v_weighted.get()),
                    "nearest_weight_r": float(v_wr.get()),
                    "nearest_weight_g": float(v_wg.get()),
                    "nearest_weight_b": float(v_wb.get()),
                    "exif_transpose": bool(v_exif.get()),
                    "jpg_quality": int(v_jpg_q.get()),
                    "png_compress_level": int(v_png_cl.get()),
                    "png_optimize": bool(v_png_opt.get()),
                    "zoom_in_factor": float(v_zoom_in.get()),
                    "zoom_out_factor": float(v_zoom_out.get()),
                    "zoom_min": float(v_zoom_min.get()),
                    "zoom_max": float(v_zoom_max.get()),
                    "canvas_bg": v_canvas_bg[0],
                    "editor_canvas_bg": v_editor_bg[0],
                    "status_fg": v_status_fg[0],
                    "status_success_fg": v_status_ok[0],
                    "status_error_fg": v_status_err[0],
                    "editor_selection_color": v_sel_color[0],
                    "editor_drag_color": v_drag_color[0],
                    "font_family": v_font_family.get().strip(),
                    "font_size": int(v_font_size.get() or 0),
                    "log_level": v_log_level.get(),
                    "log_to_console": bool(v_log_console.get()),
                    "log_to_file": bool(v_log_file.get()),
                    "watch_refresh_ms": int(v_watch_refresh.get()),
                    "show_convert_time": bool(v_show_time.get()),
                    "debug_console": bool(v_debug_console.get()),
                    "editor_grid_render_threshold": int(v_grid_threshold.get()),
                    "show_hover_coords": bool(v_show_coords.get()),
                    "continuous_drag_draw": bool(v_continuous.get()),
                    "editor_mousewheel_zoom": bool(v_editor_zoom.get()),
                })
            except (tk.TclError, ValueError) as e:
                messagebox.showerror("无效的设置", f"请检查输入：{e}", parent=win)
                return

            need_restart_keys = (
                "version_text", "kaomoji_csv", "presets_json", "recent_max",
                "palette_cache_enabled", "log_file_path", "log_max_lines",
                "block_min", "block_max", "colors_min", "colors_max",
                "preset_new_block_cap", "min_window_width", "min_window_height",
                "recent_menu_truncate", "font_family", "font_size",
            )
            need_restart = any(new_dev.get(k) != self.dev.get(k) for k in need_restart_keys)

            self.settings.update(new_settings)
            self.dev.update(new_dev)
            self._apply_settings()
            win.destroy()
            self._pref_window = None

            if need_restart:
                messagebox.showinfo("提示", "部分开发者选项需要重启程序后生效。")

        def on_cancel():
            win.destroy()
            self._pref_window = None

        tk.Button(btns, text="恢复默认", command=restore_defaults, width=10).pack(side=tk.LEFT)
        tk.Button(btns, text="取消", command=on_cancel, width=10).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(btns, text="确定", command=on_ok, width=10, bg="#2196F3", fg="white").pack(side=tk.RIGHT)

        win.protocol("WM_DELETE_WINDOW", on_cancel)

    # ============================ 开发者工具 ============================
    def _dev_generate_test(self, kind):
        size = 512
        if kind == "checker":
            img = Image.new("RGB", (size, size), (255, 255, 255))
            px = img.load()
            step = 32
            for y in range(size):
                for x in range(size):
                    if ((x // step) + (y // step)) % 2 == 0:
                        px[x, y] = (30, 30, 30)
        elif kind == "gradient":
            img = Image.new("RGB", (size, size))
            px = img.load()
            for y in range(size):
                for x in range(size):
                    px[x, y] = (int(255 * x / (size-1)), int(255 * y / (size-1)), 128)
        elif kind == "noise":
            img = Image.new("RGB", (size, size))
            px = img.load()
            for y in range(size):
                for x in range(size):
                    px[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        else:
            img = Image.new("RGB", (size, size), (240, 240, 240))
            px = img.load()
            for y in range(size):
                for x in range(size // 2):
                    c = (random.randint(30, 220), random.randint(30, 220), random.randint(30, 220))
                    px[x, y] = c
                    px[size - 1 - x, y] = c
        self.original_image = img.convert("RGBA")
        self.file_label.config(text=f"[测试] {kind}")
        self.result_image = None
        self._cached_orig_display = None
        self._cached_res_display = None
        self.current_display_size = (0, 0)
        self.is_batch_mode = False
        self.batch_images = []
        self.batch_index = 0
        self.update_nav_buttons()
        self.dirty = False
        self.show_image(self.original_image, "orig")
        self.schedule_convert(immediate=True, mark_dirty=False)
        self._dev_log(f"生成测试图：{kind} {size}×{size}", LOG_INFO)

    def _dev_benchmark(self):
        if self.original_image is None:
            messagebox.showwarning("提示", "请先加载图片")
            return
        results = []
        dither_methods = ["NONE", "FLOYDSTEINBERG", "BAYER4", "BAYER8", "ATKINSON"]
        block = self.block_var.get()
        colors = self.color_var.get()
        palette = PALETTES.get(self.palette_var.get())
        img = self.original_image.copy()
        for dm in dither_methods:
            t0 = time.time()
            try:
                self._process_image_core(img.copy(), block, colors, palette, dm)
                dt = (time.time() - t0) * 1000
                results.append(f"{dm:<18} {dt:>8.1f} ms")
            except Exception as e:
                results.append(f"{dm:<18} 失败：{e}")
        text = "性能基准（{w}×{h} 块={b} 颜色={c}）\n\n".format(
            w=img.size[0], h=img.size[1], b=block, c=colors)
        text += "\n".join(results)
        messagebox.showinfo("性能基准", text)
        self._dev_log(f"基准完成：{results}", LOG_INFO)

    def _dev_env_info(self):
        import platform
        try:
            pillow_ver = getattr(Image, "__version__", "unknown")
        except Exception:
            pillow_ver = "unknown"
        text = (
            f"PixelCraft {self.dev.get('version_text', VERSION)}\n\n"
            f"Python: {sys.version.split()[0]}\n"
            f"Tk: {tk.TkVersion}\n"
            f"Pillow: {pillow_ver}\n"
            f"平台: {platform.platform()}\n"
            f"架构: {platform.machine()}\n"
            f"可执行文件: {sys.executable}\n"
            f"运行模式: {'frozen' if getattr(sys, 'frozen', False) else 'script'}\n"
            f"tkinterdnd2: {'可用' if HAS_DND else '不可用'}\n"
            f"当前缩放: {self.zoom_factor:.3f}\n"
            f"窗口尺寸: {self.root.winfo_width()}×{self.root.winfo_height()}\n"
        )
        messagebox.showinfo("环境信息", text)

    def _dev_test_error(self):
        import traceback
        try:
            raise RuntimeError("这是一个用于测试错误处理的假异常")
        except Exception as e:
            self._dev_log(f"测试异常：{e}", LOG_ERROR)
            try:
                stack = traceback.format_exc()
            except Exception:
                stack = ""
            messagebox.showerror("测试异常", f"故意触发了一个异常，用于验证错误处理：\n\n{e}\n\n堆栈已记录到日志（如开启）。")
            if self.dev.get("debug_console", False) or self.dev.get("log_to_file", False):
                self._dev_log(stack, LOG_ERROR)

    def _dev_export_config(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON 配置", "*.json"), ("所有文件", "*.*")])
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({
                    "settings": self.settings,
                    "dev": self.dev,
                    "block_size": self.block_var.get(),
                    "colors": self.color_var.get(),
                    "last_palette": self.palette_var.get(),
                }, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("导出成功", f"配置已导出到：\n{path}")
            self._dev_log(f"导出配置：{path}", LOG_INFO)
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _dev_import_config(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON 配置", "*.json"), ("所有文件", "*.*")])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            if isinstance(cfg.get("settings"), dict):
                self.settings.update(cfg["settings"])
            if isinstance(cfg.get("dev"), dict):
                self.dev.update(cfg["dev"])
            self.save_config()
            self._apply_settings()
            messagebox.showinfo("导入成功", "配置已导入。部分设置需要重启程序后生效。")
            self._dev_log(f"导入配置：{path}", LOG_INFO)
        except Exception as e:
            messagebox.showerror("导入失败", str(e))

    def _dev_clear_palette_cache(self):
        _palette_cache.clear()
        messagebox.showinfo("完成", "调色板缓存已清空。")
        self._dev_log("调色板缓存已清空", LOG_INFO)

    def _dev_reset_config(self):
        if not messagebox.askyesno("确认", "将重置所有设置和开发者选项为默认值，并删除配置文件。确定？"):
            return
        try:
            path = os.path.join(get_base_dir(), "pixelcraft_config.json")
            if os.path.exists(path):
                os.remove(path)
            self.settings = dict(DEFAULT_SETTINGS)
            self.dev = dict(DEV_DEFAULTS)
            messagebox.showinfo("完成", "配置已重置，请重启程序。")
        except Exception as e:
            messagebox.showerror("重置失败", str(e))

    # ============================ 帮助 / 状态 ============================
    def show_help(self):
        messagebox.showinfo(
            "使用说明",
            "PixelCraft 使用说明\n\n"
            "1. 点击「选择图片」、拖拽图片或从「最近打开」载入\n"
            "2. 调整「块大小」控制像素颗粒感\n"
            "3. 调整「颜色数」或选择「色盘」控制色彩\n"
            "4. 点击「编辑像素画」进入编辑器\n"
            "   画笔 / 橡皮 / 框选 / 填充 / 吸管\n"
            "   快捷键：Ctrl+Z 撤销 / Ctrl+Y 重做 / Delete 清空选区 / Esc 关闭\n"
            "5. 点击「对比视图」左右对比原图和像素画\n"
            "6. 点击「保存像素画」导出为 PNG/JPG/BMP\n"
            "7. 点击「导出 SVG」生成矢量图\n"
            "8. 「首选项」中的「开发者」页提供大量调试参数和工具\n\n"
            "F12 打开/关闭实时监视窗口\n"
            "主窗口快捷键：Ctrl+O 打开 / Ctrl+S 保存 / Ctrl+E 编辑 / Ctrl+, 首选项 / Ctrl+Q 退出\n"
            "鼠标滚轮可缩放图片，双击恢复"
        )

    def check_update(self):
        messagebox.showinfo(
            "检查更新",
            f"更新功能正在设计中，后续版本将可以使用。\n\n当前版本：{self.dev.get('version_text', VERSION)}"
        )

    def show_about(self):
        messagebox.showinfo(
            "关于 PixelCraft",
            f"PixelCraft {self.dev.get('version_text', VERSION)} {self.kaomoji}\n\n"
            "将任意图片转换为像素画的桌面工具。\n\n"
            "作者: Grass114\n许可: MIT License\nGitHub: https://github.com/Grass114/PixelCraft"
        )

    def update_status(self, msg, kind="info"):
        if not hasattr(self, "status"):
            return
        if kind == "success":
            fg = self.dev.get("status_success_fg", "green")
        elif kind == "error":
            fg = self.dev.get("status_error_fg", "red")
        else:
            fg = self.dev.get("status_fg", "blue")
        try:
            self.status.config(text=msg, fg=fg)
        except Exception:
            pass


if __name__ == "__main__":
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = PixelCraft(root)
    root.mainloop()