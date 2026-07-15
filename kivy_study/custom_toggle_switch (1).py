from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.properties import BooleanProperty, ColorProperty
from kivy.metrics import dp

# Lock the window to your 7-inch Raspberry Pi resolution
Window.size = (800, 480)

# ==========================================
# 1. THE KV DESIGN FOR THE BUTTON SHAPE
# ==========================================
# We load this first so Kivy knows how to draw our custom button
Builder.load_string('''
<UlangToggleButton>:
    # Step 1: Strip away the ugly default gray Kivy button graphics
    background_color: 0, 0, 0, 0
    background_normal: ''
    background_down: ''
    
    # Optional: Make sure text is always white
    color: 1, 1, 1, 1
    
    # Step 2: Draw our own perfect pill-shaped background
    canvas.before:
        Color:
            # If the button is physically being pressed down, show the flash color
            # Otherwise, show its current ON/OFF color state
            rgba: self.color_pressed if self.state == 'down' else self.current_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            # This is the magic math! By making the radius exactly half of the height, 
            # you get a perfect pill shape no matter how big the button gets.
            radius: [self.height / 2]
''')

# ==========================================
# 2. THE PYTHON CLASS (The Logic)
# ==========================================
class UlangToggleButton(Button):
    """A standard Kivy button customized into a pill-shaped switch."""
    
    # Our new property to decide how the button acts
    is_toggleable = BooleanProperty(True)
    is_active = BooleanProperty(False)
    
    # Color palette
    color_on = ColorProperty([0.1, 0.6, 0.2, 1])       # Ulang Green
    color_off = ColorProperty([0.25, 0.25, 0.25, 1])   # Dark Gray
    color_pressed = ColorProperty([0.4, 0.4, 0.4, 1])  # Light flash when tapped
    
    # This tracks the actual color being shown right now
    current_color = ColorProperty([0.25, 0.25, 0.25, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure it starts with the correct color when the app boots
        self.current_color = self.color_on if self.is_active else self.color_off

    def on_release(self, *args):
        super().on_release(*args)
        
        # If it is a toggle switch, flip the state
        if self.is_toggleable:
            self.is_active = not self.is_active
        else:
            # If it's a standard button, just print the action (or run a function)
            print(f"[{self.text}] Standard Push Triggered!")

    def on_is_active(self, instance, value):
        """Kivy instantly runs this when 'is_active' flips."""
        if value:
            self.current_color = self.color_on
        else:
            self.current_color = self.color_off


# ==========================================
# 3. THE MAIN DASHBOARD LAYOUT
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
            text: "Standard Button Toggle Demo"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            font_style: "H5"
            bold: True

        # 1. Toggleable Button (ON)
        UlangToggleButton:
            text: "AERATOR (TOGGLE)"
            font_size: "18sp"
            size_hint_x: 0.6
            size_hint_y: None
            height: dp(60)
            pos_hint: {"center_x": .5}
            
            is_toggleable: True 
            is_active: True 

        # 2. Toggleable Button (OFF)
        UlangToggleButton:
            text: "WATER PUMP (TOGGLE)"
            font_size: "18sp"
            size_hint_x: 0.6
            size_hint_y: None
            height: dp(60)
            pos_hint: {"center_x": .5}
            
            is_toggleable: True
            is_active: False

        # 3. Standard Non-Toggleable Button
        UlangToggleButton:
            text: "SYSTEM FLUSH (PUSH)"
            font_size: "18sp"
            size_hint_x: 0.6
            size_hint_y: None
            height: dp(60)
            pos_hint: {"center_x": .5}
            
            # This turns off the memory, making it a normal button!
            is_toggleable: False
            
            # Since it defaults to 'OFF', we just change the off color to Red!
            color_off: 0.8, 0.2, 0.2, 1
            color_pressed: 0.9, 0.4, 0.4, 1
'''

class CustomSwitchApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)

if __name__ == '__main__':
    CustomSwitchApp().run()