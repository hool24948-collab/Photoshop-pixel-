# -*- coding: utf-8 -*-
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter
from kivy.uix.anchorlayout import AnchorLayout
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.graphics.texture import Texture
import xml.etree.ElementTree as ET

class ColorPreviewWidget(Widget):
    """Кружок для отображения текущего выбранного цвета"""
    def __init__(self, **kwargs):
        super(ColorPreviewWidget, self).__init__(**kwargs)
        with self.canvas:
            self.color_instruction = Color(1, 0, 0, 1)
            self.circle = Ellipse(size=(36, 36), pos=(0, 0))
        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def update_graphics(self, *args):
        self.circle.pos = (self.center_x - 18, self.center_y - 18)

    def set_color(self, rgba):
        self.color_instruction.rgba = rgba

class PixelCanvas(Widget):
    """Холст 32x32 с четкой сеткой, калькой и экспортом в SVG/PNG"""
    def __init__(self, size_cells=32, **kwargs):
        super(PixelCanvas, self).__init__(**kwargs)
        self.cols = size_cells
        self.rows = size_cells
        
        self.base_color = [1.0, 0.0, 0.0, 1.0]
        self.alpha = 1.0
        self.brightness = 1.0
        self.current_color = (1.0, 0.0, 0.0, 1.0)
        self.current_tool = 'brush'
        
        self.frames = [{}] # Список кадров анимации
        self.current_frame_index = 0
        
        self.bind(pos=self.redraw, size=self.redraw)

    def on_touch_down(self, touch):
        if self.current_tool == 'zoom':
            return super(PixelCanvas, self).on_touch_down(touch)
        if self.collide_point(*touch.pos):
            self.paint_at(touch)
            return True
        return super(PixelCanvas, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.current_tool == 'zoom':
            return super(PixelCanvas, self).on_touch_move(touch)
        if self.collide_point(*touch.pos):
            self.paint_at(touch)
            return True
        return super(PixelCanvas, self).on_touch_move(touch)

    def paint_at(self, touch):
        local_x, local_y = self.to_local(touch.x, touch.y)
        if 0 <= local_x < self.width and 0 <= local_y < self.height:
            cell_w = self.width / self.cols
            cell_h = self.height / self.rows
            
            c = int(local_x / cell_w)
            r = int(local_y / cell_h)
            
            if 0 <= r < self.rows and 0 <= c < self.cols:
                if self.current_frame_index >= len(self.frames):
                    self.frames.append({})
                current_frame = self.frames[self.current_frame_index]
                
                if self.current_tool == 'brush':
                    current_frame[(r, c)] = self.current_color
                elif self.current_tool == 'eraser':
                    if (r, c) in current_frame:
                        del current_frame[(r, c)]
                self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            # Цвет фона сетки (темные линии)
            Color(0.25, 0.25, 0.25, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            cell_w = self.width / self.cols
            cell_h = self.height / self.rows
            
            prev_frame = {}
            if self.current_frame_index > 0 and (self.current_frame_index - 1) < len(self.frames):
                prev_frame = self.frames[self.current_frame_index - 1]
                
            current_frame = self.frames[self.current_frame_index] if self.current_frame_index < len(self.frames) else {}
            gap = 1.2
            
            # 1. Калька (Onion Skin): прошлый кадр полупрозрачным
            for (r, c), rgba in prev_frame.items():
                if (r, c) not in current_frame:
                    x = self.x + c * cell_w
                    y = self.y + r * cell_h
                    Color(rgba[0], rgba[1], rgba[2], 0.2)
                    Rectangle(pos=(x + gap/2, y + gap/2), size=(cell_w - gap, cell_h - gap))

            # 2. Отрисовка текущего кадра
            for r in range(self.rows):
                for c in range(self.cols):
                    x = self.x + c * cell_w
                    y = self.y + r * cell_h
                    
                    if (r, c) in current_frame:
                        rgba = current_frame[(r, c)]
                        Color(rgba[0], rgba[1], rgba[2], rgba[3])
                        Rectangle(pos=(x + gap/2, y + gap/2), size=(cell_w - gap, cell_h - gap))
                    elif (r, c) not in prev_frame:
                        Color(0.9, 0.9, 0.9, 1)
                        Rectangle(pos=(x + gap/2, y + gap/2), size=(cell_w - gap, cell_h - gap))

    def update_final_color(self):
        r = self.base_color[0] * self.brightness
        g = self.base_color[1] * self.brightness
        b = self.base_color[2] * self.brightness
        a = self.alpha
        self.current_color = (max(0.0, min(1.0, r)), max(0.0, min(1.0, g)), max(0.0, min(1.0, b)), a)

    def set_base_color(self, rgb):
        self.base_color = [rgb[0], rgb[1], rgb[2], 1.0]
        self.update_final_color()
        if self.current_tool == 'zoom':
            self.current_tool = 'brush'

    def set_brightness(self, value):
        self.brightness = value
        self.update_final_color()

    def set_alpha(self, value):
        self.alpha = value
        self.update_final_color()

    def set_tool(self, tool_name):
        self.current_tool = tool_name

    def next_frame(self):
        self.current_frame_index += 1
        if self.current_frame_index >= len(self.frames):
            self.frames.append({})
        self.redraw()

    def prev_frame(self):
        if self.current_frame_index > 0:
            self.current_frame_index -= 1
            self.redraw()

    def export_to_svg(self):
        filename = f"pixel_art_frame_{self.current_frame_index + 1}.svg"
        public_dir = "/sdcard/Pictures"
        if not os.path.exists(public_dir):
            try:
                os.makedirs(public_dir, exist_ok=True)
            except:
                public_dir = App.get_running_app().user_data_dir
                
        filepath = os.path.join(public_dir, filename)
        
        svg_root = ET.Element("svg", xmlns="http://www.w3.org/2000/svg", 
                              viewBox=f"0 0 {self.cols} {self.rows}", 
                              width="1024", height="1024")
        
        current_frame = self.frames[self.current_frame_index] if self.current_frame_index < len(self.frames) else {}
        for (r, c), color in current_frame.items():
            hex_color = '#{:02x}{:02x}{:02x}'.format(
                int(color[0]*255), int(color[1]*255), int(color[2]*255)
            )
            y_svg = self.rows - 1 - r
            ET.SubElement(svg_root, "rect", x=str(c), y=str(y_svg), width="1", height="1", fill=hex_color)
            
        tree = ET.ElementTree(svg_root)
        tree.write(filepath)
        return filepath

    def export_to_png(self):
        filename = f"pixel_art_frame_{self.current_frame_index + 1}.png"
        public_dir = "/sdcard/Pictures"
        if not os.path.exists(public_dir):
            try:
                os.makedirs(public_dir, exist_ok=True)
            except:
                public_dir = App.get_running_app().user_data_dir
                
        filepath = os.path.join(public_dir, filename)
        
        buf = bytearray()
        current_frame = self.frames[self.current_frame_index] if self.current_frame_index < len(self.frames) else {}
        
        for r in range(self.rows - 1, -1, -1):
            for c in range(self.cols):
                color = current_frame.get((r, c), (1.0, 1.0, 1.0, 1.0))
                buf.append(int(color[0] * 255))
                buf.append(int(color[1] * 255))
                buf.append(int(color[2] * 255))
                buf.append(int(color[3] * 255))
                
        texture = Texture.create(size=(self.cols, self.rows), colorfmt='rgba')
        texture.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
        texture.save(filepath)
        return filepath

class PixelEditorApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical', padding=4, spacing=4)
        
        # 1. Верхняя панель (Кадр + Превью цвета)
        top_bar = BoxLayout(size_hint_y=None, height=38, spacing=8)
        self.info_label = Button(
            text="Frame: 1", 
            background_color=(0.15, 0.15, 0.15, 1),
            background_normal='',
            font_size=14
        )
        top_bar.add_widget(self.info_label)
        
        self.color_preview = ColorPreviewWidget(size_hint=(None, None), size=(38, 38))
        top_bar.add_widget(self.color_preview)
        root.add_widget(top_bar)
        
        # 2. Центр: Холст в Scatter для зума
        center_container = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1, 1))
        
        self.scatter = Scatter(
            size_hint=(None, None),
            size=(240, 240),
            do_rotation=False,
            scale_min=1.0,
            scale_max=4.0,
            do_translation=False,
            do_scale=True
        )
        
        self.canvas_widget = PixelCanvas(size_cells=32, size_hint=(None, None), size=(240, 240))
        self.scatter.add_widget(self.canvas_widget)
        center_container.add_widget(self.scatter)
        root.add_widget(center_container)
        
        # 3. Инструменты: Кисть, Ластик, Режим перемещения
        tools_layout = BoxLayout(size_hint_y=None, height=36, spacing=4)
        
        self.btn_brush = Button(text="✏️ Brush", background_color=(0.1, 0.7, 0.3, 1), background_normal='', font_size=12)
        self.btn_brush.bind(on_press=lambda x: self.select_tool('brush'))
        
        self.btn_eraser = Button(text="🧹 Eraser", background_color=(0.5, 0.5, 0.5, 1), background_normal='', font_size=12)
        self.btn_eraser.bind(on_press=lambda x: self.select_tool('eraser'))
        
        self.btn_zoom = Button(text="✋ Move", background_color=(0.6, 0.3, 0.7, 1), background_normal='', font_size=12)
        self.btn_zoom.bind(on_press=lambda x: self.select_tool('zoom'))
        
        tools_layout.add_widget(self.btn_brush)
        tools_layout.add_widget(self.btn_eraser)
        tools_layout.add_widget(self.btn_zoom)
        root.add_widget(tools_layout)
        
        # Кнопки приближения / отдаления
        zoom_layout = BoxLayout(size_hint_y=None, height=34, spacing=4)
        btn_zoom_out = Button(text="🔍➖ Zoom Out", background_color=(0.35, 0.35, 0.5, 1), background_normal='', font_size=11)
        btn_zoom_out.bind(on_press=self.zoom_out)
        btn_zoom_in = Button(text="🔍➕ Zoom In", background_color=(0.35, 0.35, 0.5, 1), background_normal='', font_size=11)
        btn_zoom_in.bind(on_press=self.zoom_in)
        zoom_layout.add_widget(btn_zoom_out)
        zoom_layout.add_widget(btn_zoom_in)
        root.add_widget(zoom_layout)
        
        # Слайдеры (Яркость и Альфа)
        sliders_layout = BoxLayout(size_hint_y=None, height=34, spacing=4)
        sliders_layout.add_widget(Label(text="Bright", size_hint_x=None, width=40, font_size=11))
        slider_bright = Slider(min=0.1, max=1.0, value=1.0)
        slider_bright.bind(value=lambda inst, val: self.update_brightness(val))
        sliders_layout.add_widget(slider_bright)
        
        sliders_layout.add_widget(Label(text="Alpha", size_hint_x=None, width=35, font_size=11))
        slider_alpha = Slider(min=0.1, max=1.0, value=1.0)
        slider_alpha.bind(value=lambda inst, val: self.update_alpha(val))
        sliders_layout.add_widget(slider_alpha)
        root.add_widget(sliders_layout)
        
        # Палитра цветов
        palette_layout = BoxLayout(size_hint_y=None, height=34, spacing=2)
        colors = [
            (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), 
            (1.0, 1.0, 0.0), (1.0, 0.5, 0.0), (0.5, 0.0, 0.5), 
            (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)
        ]
        for rgb in colors:
            col_btn = Button(background_color=(rgb[0], rgb[1], rgb[2], 1.0), background_normal='')
            col_btn.bind(on_press=lambda inst, col=rgb: self.select_color_ui(col))
            palette_layout.add_widget(col_btn)
        root.add_widget(palette_layout)
        
        # Управление кадрами и сохранение (PNG и SVG)
        actions_layout = BoxLayout(size_hint_y=None, height=36, spacing=4)
        btn_prev = Button(text="< Prev", background_color=(0.3, 0.3, 0.3, 1), background_normal='', font_size=12)
        btn_prev.bind(on_press=self.prev_frame_ui)
        
        btn_next = Button(text="Next >", background_color=(0.3, 0.3, 0.3, 1), background_normal='', font_size=12)
        btn_next.bind(on_press=self.next_frame_ui)
        
        btn_png = Button(text="💾 Save PNG", background_color=(0.1, 0.6, 0.8, 1), background_normal='', font_size=12)
        btn_png.bind(on_press=self.save_png_ui)

        btn_svg = Button(text="📐 Save SVG", background_color=(0.1, 0.7, 0.3, 1), background_normal='', font_size=12)
        btn_svg.bind(on_press=self.save_svg_ui)
        
        actions_layout.add_widget(btn_prev)
        actions_layout.add_widget(btn_next)
        actions_layout.add_widget(btn_png)
        actions_layout.add_widget(btn_svg)
        root.add_widget(actions_layout)
        
        self.color_preview.set_color(self.canvas_widget.current_color)
        return root

    def save_png_ui(self, instance):
        self.canvas_widget.export_to_png()
        self.info_label.text = "Saved to Pictures!"

    def save_svg_ui(self, instance):
        self.canvas_widget.export_to_svg()
        self.info_label.text = "Saved SVG!"

    def zoom_in(self, instance):
        if self.scatter.scale < self.scatter.scale_max:
            self.scatter.scale = min(self.scatter.scale_max, self.scatter.scale + 0.5)

    def zoom_out(self, instance):
        if self.scatter.scale > self.scatter.scale_min:
            self.scatter.scale = max(self.scatter.scale_min, self.scatter.scale - 0.5)

    def select_tool(self, tool_name):
        self.canvas_widget.set_tool(tool_name)
        if tool_name == 'zoom':
            self.scatter.do_translation = True
            self.btn_zoom.background_color = (0.2, 0.8, 0.4, 1)
            self.btn_brush.background_color = (0.2, 0.5, 0.8, 1)
            self.btn_eraser.background_color = (0.5, 0.5, 0.5, 1)
        else:
            self.scatter.do_translation = False
            self.btn_zoom.background_color = (0.6, 0.3, 0.7, 1)
            if tool_name == 'brush':
                self.btn_brush.background_color = (0.1, 0.7, 0.3, 1)
                self.btn_eraser.background_color = (0.5, 0.5, 0.5, 1)
            else:
                self.btn_brush.background_color = (0.2, 0.5, 0.8, 1)
                self.btn_eraser.background_color = (0.1, 0.7, 0.3, 1)

    def select_color_ui(self, rgb):
        self.canvas_widget.select_color_ui_rgb = rgb if hasattr(self.canvas_widget, 'select_color_ui_rgb') else None
        self.canvas_widget.set_base_color(rgb)
        self.color_preview.set_color(self.canvas_widget.current_color)
        self.select_tool('brush')

    def update_brightness(self, val):
        self.canvas_widget.set_brightness(val)
        self.color_preview.set_color(self.canvas_widget.current_color)

    def update_alpha(self, val):
        self.canvas_widget.set_alpha(val)
        self.color_preview.set_color(self.canvas_widget.current_color)

    def next_frame_ui(self, instance):
        self.canvas_widget.next_frame()
        self.info_label.text = f"Frame: {self.canvas_widget.current_frame_index + 1}"

    def prev_frame_ui(self, instance):
        self.canvas_widget.prev_frame()
        self.info_label.text = f"Frame: {self.canvas_widget.current_frame_index + 1}"

if __name__ == '__main__':
    PixelEditorApp().run()
