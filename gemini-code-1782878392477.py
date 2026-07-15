from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window

# Lock the window to your exact 7-inch touchscreen resolution (Landscape)
Window.size = (800, 480)

# Kivy Design Language (KV) string to structure the UI
KV = '''
BoxLayout:
    orientation: 'vertical'
    padding: 10
    spacing: 10
    canvas.before:
        Color:
            rgba: 0.12, 0.12, 0.12, 1  # Dark industrial background
        Rectangle:
            pos: self.pos
            size: self.size

    # TOP SECTION (Camera on Left, Controls on Right)
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: 0.85
        spacing: 10

        # LEFT PANE: AI Camera Feed Placeholder (60% width)
        Label:
            text: "LIVE YOLOv8 CAMERA FEED\\n\\n(Bounding Boxes Overlay Area)"
            font_size: '18sp'
            bold: True
            color: 0.5, 0.5, 0.5, 1
            size_hint_x: 0.6
            halign: 'center'
            canvas.before:
                Color:
                    rgba: 0, 0, 0, 1  # Black background for camera feed
                Rectangle:
                    pos: self.pos
                    size: self.size

        # RIGHT PANE: Status & Hardware Toggles (40% width)
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.4
            spacing: 15

            # Top Right: Sensor Status Indicators
            GridLayout:
                cols: 2
                size_hint_y: 0.4
                canvas.before:
                    Color:
                        rgba: 0.2, 0.2, 0.2, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                
                Label:
                    text: "Water Temp:"
                    font_size: '16sp'
                Label:
                    text: "28.5 °C"
                    font_size: '18sp'
                    bold: True
                    color: 0.2, 0.8, 0.2, 1  # Green safe status
                
                Label:
                    text: "Water Level:"
                    font_size: '16sp'
                Label:
                    text: "NORMAL"
                    font_size: '18sp'
                    bold: True
                    color: 0.2, 0.8, 0.2, 1
                
                Label:
                    text: "Volume:"
                    font_size: '16sp'
                Label:
                    text: "2.5 L"
                    font_size: '18sp'
                    bold: True

            # Middle Right: Hardware Deployment Switches
            GridLayout:
                cols: 2
                size_hint_y: 0.6
                spacing: 5
                padding: [10, 10, 10, 10]
                
                Label:
                    text: "Aerator"
                    font_size: '16sp'
                Switch:
                    active: True
                
                Label:
                    text: "Temp Control"
                    font_size: '16sp'
                Switch:
                    active: False
                
                Label:
                    text: "LED Panels"
                    font_size: '16sp'
                Switch:
                    active: True

    # BOTTOM BAR: Primary Action Button
    Button:
        text: "START BATCH COUNT"
        size_hint_y: 0.15
        font_size: '22sp'
        bold: True
        background_normal: ''
        background_color: 0.1, 0.6, 0.2, 1  # High contrast green button
'''

class UlangDashboardApp(App):
    def build(self):
        self.title = "Ulang Automated Counting System"
        return Builder.load_string(KV)

if __name__ == '__main__':
    UlangDashboardApp().run()