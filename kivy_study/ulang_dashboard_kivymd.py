from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.metrics import dp

# Lock the window to your exact 7-inch touchscreen resolution (Landscape)
# This perfectly mimics the physical Raspberry Pi 5 display.
Window.size = (800, 480)

# Kivy Design Language (KV) string to structure the highly stylized UI
KV = '''
MDScreen:
    # Set the overall background to a dark industrial gray
    md_bg_color: 0.08, 0.08, 0.08, 1 

    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(12)
        spacing: dp(15)

        # ==========================================
        # TOP SECTION: 60/40 Split Layout
        # ==========================================
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.85
            spacing: dp(15)

            # --------------------------------------
            # LEFT PANE: Camera Feed (60%)
            # --------------------------------------
            # MDCard provides a nice rounded container with a subtle shadow
            MDCard:
                size_hint_x: 0.6
                md_bg_color: 0, 0, 0, 1  # True black for video feed
                radius: [16, 16, 16, 16]
                elevation: 2
                line_color: 0.2, 0.2, 0.2, 1
                line_width: 1
                
                # Placeholder for the OpenCV Image Feed
                MDLabel:
                    text: "LIVE YOLOv8 CAMERA FEED\\n\\n[size=14][color=#666666](Awaiting OpenCV Video Stream)[/color][/size]"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.8, 0.8, 0.8, 1
                    markup: True
                    font_style: "H6"
                    bold: True

            # --------------------------------------
            # RIGHT PANE: Data & Controls (40%)
            # --------------------------------------
            MDBoxLayout:
                orientation: 'vertical'
                size_hint_x: 0.4
                spacing: dp(15)

                # TOP RIGHT: Status Indicators
                MDCard:
                    orientation: 'vertical'
                    size_hint_y: 0.45
                    md_bg_color: 0.15, 0.15, 0.15, 1
                    radius: [16, 16, 16, 16]
                    padding: dp(12)
                    spacing: dp(5)

                    MDLabel:
                        text: "SYSTEM STATUS"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.6, 0.6, 0.6, 1
                        bold: True
                        size_hint_y: 0.2

                    GridLayout:
                        cols: 2
                        size_hint_y: 0.8
                        
                        # Water Temperature (Green = Safe)
                        MDLabel:
                            text: "Water Temp:"
                            theme_text_color: "Custom"
                            text_color: 0.8, 0.8, 0.8, 1
                            font_size: '16sp'
                        MDLabel:
                            text: "28.5 °C"
                            theme_text_color: "Custom"
                            text_color: 0.2, 0.8, 0.2, 1  # Bright Green
                            bold: True
                            font_size: '18sp'
                            halign: 'right'
                            
                        # Water Level (Green = Normal)
                        MDLabel:
                            text: "Water Level:"
                            theme_text_color: "Custom"
                            text_color: 0.8, 0.8, 0.8, 1
                            font_size: '16sp'
                        MDLabel:
                            text: "NORMAL"
                            theme_text_color: "Custom"
                            text_color: 0.2, 0.8, 0.2, 1  # Bright Green
                            bold: True
                            font_size: '18sp'
                            halign: 'right'

                        # Water Volume (Red = Warning/Low)
                        MDLabel:
                            text: "Volume:"
                            theme_text_color: "Custom"
                            text_color: 0.8, 0.8, 0.8, 1
                            font_size: '16sp'
                        MDLabel:
                            text: "2.5 L"
                            theme_text_color: "Custom"
                            text_color: 0.9, 0.2, 0.2, 1  # Bright Red Alert
                            bold: True
                            font_size: '18sp'
                            halign: 'right'

                # BOTTOM RIGHT: Hardware Toggles
                MDCard:
                    orientation: 'vertical'
                    size_hint_y: 0.55
                    md_bg_color: 0.15, 0.15, 0.15, 1
                    radius: [12, 12, 12, 12]
                    padding: dp(15)
                    spacing: dp(10)

                    MDLabel:
                        text: "HARDWARE DEPLOYMENT"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.6, 0.6, 0.6, 1
                        bold: True
                        size_hint_y: 0.15

                    GridLayout:
                        cols: 2
                        size_hint_y: 0.85
                        row_default_height: dp(40)
                        row_force_default: True
                        spacing: dp(5)

                        MDLabel:
                            text: "Aerator"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1
                            font_size: '16sp'
                        MDSwitch:
                            active: True
                            icon_active: "check"
                            icon_inactive: "close"

                        MDLabel:
                            text: "Temp Control"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1
                            font_size: '16sp'
                        MDSwitch:
                            active: False
                            icon_active: "check"
                            icon_inactive: "close"

                        MDLabel:
                            text: "LED Panels"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1
                            font_size: '16sp'
                        MDSwitch:
                            active: True
                            icon_active: "check"
                            icon_inactive: "close"

        # ==========================================
        # BOTTOM BAR: Primary Action
        # ==========================================
        # Standard Kivy button used here because it is easily styled into a large, 
        # blocky, touch-friendly rectangle spanning the entire bottom row.
        Button:
            text: "START BATCH COUNT"
            size_hint_y: 0.15
            font_size: '22sp'
            bold: True
            background_normal: ''
            background_color: 0.1, 0.5, 0.2, 1  # Deep industrial green
            # Add rounded corners to standard Kivy button via Canvas
            canvas.before:
                Color:
                    rgba: self.background_color
                RoundedRectangle:
                    size: self.size
                    pos: self.pos
                    radius: [8]
'''

class UlangSystemApp(MDApp):
    def build(self):
        # Set the overarching theme colors for KivyMD
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        
        # Load and return the KV string layout
        return Builder.load_string(KV)

if __name__ == '__main__':
    UlangSystemApp().run()