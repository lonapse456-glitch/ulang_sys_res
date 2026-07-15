from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.uix.button import MDFillRoundFlatButton
from kivy.properties import BooleanProperty, ColorProperty
from kivy.metrics import dp

# Lock the window to your 7-inch Raspberry Pi resolution
Window.size = (800, 480)

# ==========================================
# 1. THE PYTHON CLASS (The Logic)
# ==========================================
class UlangToggleButton(MDFillRoundFlatButton):
    """A custom rounded button that acts like a switch."""
    
    # We give the button its own boolean variable to remember if it is ON or OFF
    is_active = BooleanProperty(False)
    
    # We define the colors we want it to shift between
    color_on = ColorProperty([0.1, 0.6, 0.2, 1])   # Ulang Green
    color_off = ColorProperty([0.25, 0.25, 0.25, 1]) # Dark Gray

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set the starting color
        self.md_bg_color = self.color_off

    def on_release(self, *args):
        """Fired every time the technician taps the button."""
        # Flip the state from True to False, or False to True
        self.is_active = not self.is_active

    def on_is_active(self, instance, value):
        """Kivy automatically runs this function the moment 'is_active' changes!"""
        if value:
            self.md_bg_color = self.color_on
            # You can also change the text here if you want!
            # self.text = f"{self.text.split(' ')[0]} (ON)" 
        else:
            self.md_bg_color = self.color_off
            # self.text = f"{self.text.split(' ')[0]} (OFF)"


# ==========================================
# 2. THE KV DESIGN (The Layout)
# ==========================================
KV = '''
MDScreen:
    md_bg_color: 0.08, 0.08, 0.08, 1

    MDBoxLayout:
        orientation: 'vertical'
        spacing: dp(30)
        pos_hint: {"center_x": .5, "center_y": .5}
        adaptive_height: True

        MDLabel:
            text: "Hardware Controls"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            font_style: "H5"
            bold: True

        # Now you can use your custom button exactly like a standard widget!
        UlangToggleButton:
            id: btn_aerator
            text: "AERATOR"
            font_size: "18sp"
            size_hint_x: 0.6
            height: dp(60)
            pos_hint: {"center_x": .5}
            
            # Start it in the ON state
            is_active: True 

        UlangToggleButton:
            id: btn_pump
            text: "WATER PUMP"
            font_size: "18sp"
            size_hint_x: 0.6
            height: dp(60)
            pos_hint: {"center_x": .5}
            
            # Start it in the OFF state
            is_active: False
'''

class CustomSwitchApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)

if __name__ == '__main__':
    CustomSwitchApp().run()