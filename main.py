import kivy
kivy.require('2.1.0')
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.utils import platform
from PIL import Image as PILImage
from pixel_core import process_image, PALETTES

class PixelCraftLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.original_image = None
        self.result_image = None
        self.build_ui()

    def build_ui(self):
        self.orientation = 'vertical'
        # 控制栏
        control = BoxLayout(size_hint_y=0.15, spacing=5)
        control.add_widget(Button(text='选择图片', on_press=self.select_image))
        control.add_widget(Label(text='块大小'))
        self.block_slider = Slider(min=2, max=40, value=12)
        control.add_widget(self.block_slider)
        control.add_widget(Label(text='颜色数'))
        self.color_slider = Slider(min=2, max=64, value=16)
        control.add_widget(self.color_slider)
        self.palette_spinner = Spinner(text='自动', values=list(PALETTES.keys()))
        control.add_widget(self.palette_spinner)
        self.convert_btn = Button(text='转换', on_press=self.convert_image)
        control.add_widget(self.convert_btn)
        self.save_btn = Button(text='保存', on_press=self.save_image)
        self.save_btn.disabled = True
        control.add_widget(self.save_btn)
        self.add_widget(control)

        # 图片预览
        preview = BoxLayout()
        self.orig_img = Image()
        self.res_img = Image()
        preview.add_widget(self.orig_img)
        preview.add_widget(self.res_img)
        self.add_widget(preview)

        # 状态栏
        self.status = Label(text='就绪', size_hint_y=0.05)
        self.add_widget(self.status)

        # 实时转换（滑块变化时自动转换）
        self.block_slider.bind(value=self.on_slider_change)
        self.color_slider.bind(value=self.on_slider_change)
        self.palette_spinner.bind(text=self.on_slider_change)

    def on_slider_change(self, *args):
        if self.original_image:
            Clock.schedule_once(lambda dt: self.convert_image(None), 0.2)

    def select_image(self, instance):
        content = FileChooserListView()
        popup = Popup(title='选择图片', content=content, size_hint=(0.9,0.9))
        content.bind(on_selection=lambda x, selection: self.load_image(selection[0], popup))
        popup.open()

    def load_image(self, path, popup):
        popup.dismiss()
        try:
            self.original_image = PILImage.open(path).convert('RGBA')
            self.display_image(self.original_image, self.orig_img)
            self.status.text = f'已加载: {path.split("/")[-1]}'
            self.convert_image(None)
        except Exception as e:
            self.status.text = f'加载失败: {str(e)}'

    def convert_image(self, instance):
        if not self.original_image:
            return
        block = int(self.block_slider.value)
        colors = int(self.color_slider.value)
        palette_name = self.palette_spinner.text
        palette = PALETTES.get(palette_name)
        try:
            result = process_image(self.original_image.copy(), block, colors, palette)
            self.result_image = result
            self.display_image(result, self.res_img)
            self.save_btn.disabled = False
            self.status.text = f'转换完成 | 网格 {result.width//block}×{result.height//block}'
        except Exception as e:
            self.status.text = f'转换错误: {str(e)}'

    def display_image(self, pil_img, kivy_img):
        pil_img = pil_img.convert('RGBA')
        data = pil_img.tobytes()
        texture = Texture.create(size=pil_img.size, colorfmt='rgba')
        texture.blit_buffer(data, colorfmt='rgba', bufferfmt='ubyte')
        kivy_img.texture = texture

    def save_image(self, instance):
        if not self.result_image:
            return
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
            from android.storage import app_storage_path
            path = app_storage_path() + '/pixel_output.png'
        else:
            path = 'pixel_output.png'
        self.result_image.save(path)
        self.status.text = f'已保存到: {path}'

class PixelCraftApp(App):
    def build(self):
        return PixelCraftLayout()

if __name__ == '__main__':
    PixelCraftApp().run()