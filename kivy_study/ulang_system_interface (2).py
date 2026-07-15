from kivy.config import Config
# Force Kivy to use the onscreen virtual keyboard for the 7-inch touchscreen
Config.set('kivy', 'keyboard_mode', 'systemandmulti')

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.graphics import Color, Line

# ---------------------------------------------------------
# HARDWARE GPIO SETUP (Fail-safe for Windows/Mac testing)
# ---------------------------------------------------------
try:
    from gpiozero import Button as HardwareButton
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: gpiozero not found. Physical GPIO buttons disabled (Running on Laptop).")

# Lock the window to the exact 7-inch touchscreen resolution
Window.size = (800, 480)

KV = '''
# ---------------------------------------------------------
# SCREEN MANAGER (Handles page transitions)
# ---------------------------------------------------------
ScreenManager:
    DashboardScreen:
        id: dashboard_screen
    SettingsScreen:
        id: settings_screen

# ---------------------------------------------------------
# PAGE 1: THE MAIN DASHBOARD
# ---------------------------------------------------------
<DashboardScreen>:
    name: "dashboard"
    md_bg_color: 0.08, 0.08, 0.08, 1  # Dark industrial gray

    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(15)
        spacing: dp(15)

        # TOP BAR: Title & Settings Icon
        MDBoxLayout:
            size_hint_y: None
            height: dp(40)
            MDLabel:
                text: "ULANG AI COUNTING SYSTEM"
                font_style: "H6"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                bold: True
            
            MDIconButton:
                id: btn_settings
                icon: "cog"
                theme_text_color: "Custom"
                text_color: 0.8, 0.8, 0.8, 1
                pos_hint: {"center_y": .5}
                on_release: 
                    app.go_to_settings()

        # MIDDLE SECTION: 60/40 Split Layout
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.75
            spacing: dp(15)

            # LEFT PANE: Camera Feed (60%)
            MDCard:
                size_hint_x: 0.6
                md_bg_color: 0, 0, 0, 1
                radius: [12, 12, 12, 12]
                elevation: 2
                MDLabel:
                    text: "LIVE YOLOv8 CAMERA FEED\\n\\n[size=14][color=#666666](Awaiting OpenCV Video Stream)[/color][/size]"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.8, 0.8, 0.8, 1
                    markup: True
                    bold: True

            # RIGHT PANE: Data & Controls (40%)
            MDBoxLayout:
                orientation: 'vertical'
                size_hint_x: 0.4
                spacing: dp(15)

                # TOP RIGHT: Status Indicators
                MDCard:
                    orientation: 'vertical'
                    size_hint_y: 0.45
                    md_bg_color: 0.15, 0.15, 0.15, 1
                    radius: [12]
                    padding: dp(15)
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
                        
                        MDLabel:
                            text: "Water Temp:"
                            theme_text_color: "Custom"
                            text_color: 0.8, 0.8, 0.8, 1
                        MDLabel:
                            text: "28.5 °C"
                            theme_text_color: "Custom"
                            text_color: 0.2, 0.8, 0.2, 1  # Green
                            bold: True
                            halign: 'right'
                            
                        MDLabel:
                            text: "Water Level:"
                            theme_text_color: "Custom"
                            text_color: 0.8, 0.8, 0.8, 1
                        MDLabel:
                            text: "NORMAL"
                            theme_text_color: "Custom"
                            text_color: 0.2, 0.8, 0.2, 1  # Green
                            bold: True
                            halign: 'right'

                        MDLabel:
                            text: "Volume:"
                            theme_text_color: "Custom"
                            text_color: 0.8, 0.8, 0.8, 1
                        MDLabel:
                            text: "2.5 L"
                            theme_text_color: "Custom"
                            text_color: 0.9, 0.2, 0.2, 1  # Red Warning
                            bold: True
                            halign: 'right'

                # BOTTOM RIGHT: Hardware Toggles
                MDCard:
                    orientation: 'vertical'
                    size_hint_y: 0.55
                    md_bg_color: 0.15, 0.15, 0.15, 1
                    radius: [12]
                    padding: dp(15)

                    MDLabel:
                        text: "HARDWARE DEPLOYMENT"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.6, 0.6, 0.6, 1
                        bold: True
                        size_hint_y: 0.2

                    GridLayout:
                        cols: 2
                        size_hint_y: 0.8
                        row_default_height: dp(35)
                        row_force_default: True

                        MDLabel:
                            text: "Aerator"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1
                        MDSwitch:
                            id: sw_aerator
                            active: True

                        MDLabel:
                            text: "Temp Control"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1
                        MDSwitch:
                            id: sw_temp
                            active: False

                        MDLabel:
                            text: "LED Panels"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1
                        MDSwitch:
                            id: sw_led
                            active: True

        # BOTTOM BAR: Action Button
        MDFillRoundFlatButton:
            id: start_btn
            text: "START BATCH COUNT"
            size_hint_x: 1
            size_hint_y: 0.15
            font_size: '20sp'
            md_bg_color: 0.1, 0.5, 0.2, 1
            radius: [15]
            on_release: app.start_batch_count()

# ---------------------------------------------------------
# PAGE 2: THE SETTINGS SCREEN (From Blueprint)
# ---------------------------------------------------------
<SettingsScreen>:
    name: "settings"
    md_bg_color: 0.08, 0.08, 0.08, 1

    MDBoxLayout:
        orientation: 'vertical'

        # Custom Top Navigation Bar
        MDTopAppBar:
            title: "System Configuration"
            md_bg_color: 0.15, 0.15, 0.15, 1
            specific_text_color: 1, 1, 1, 1
            left_action_items: [["arrow-left", lambda x: app.go_to_dashboard()]]
            elevation: 0

        # Scrollable Settings List
        ScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                adaptive_height: True
                padding: dp(20)
                spacing: dp(30)

                # 1. AI Vision Tuning
                MDLabel:
                    text: "1. AI Vision Tuning (YOLOv8)"
                    theme_text_color: "Custom"
                    text_color: 0.2, 0.8, 0.2, 1
                    font_style: "Subtitle1"
                    bold: True
                MDBoxLayout:
                    orientation: 'vertical'
                    adaptive_height: True
                    spacing: dp(5)
                    MDLabel:
                        text: "Confidence Threshold (%)"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                    MDSlider:
                        min: 10
                        max: 100
                        value: 80
                        color: 0.1, 0.5, 0.2, 1
                    MDLabel:
                        text: "Camera Exposure/Brightness"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                    MDSlider:
                        min: 0
                        max: 100
                        value: 50

                # 2. Environmental Alarm Thresholds
                MDLabel:
                    text: "2. Environmental Alarm Thresholds"
                    theme_text_color: "Custom"
                    text_color: 0.2, 0.8, 0.2, 1
                    font_style: "Subtitle1"
                    bold: True
                MDBoxLayout:
                    orientation: 'vertical'
                    adaptive_height: True
                    spacing: dp(15)
                    MDTextField:
                        hint_text: "Max Temperature Limit (°C)"
                        text_color_normal: 1, 1, 1, 1
                        input_type: 'number' 
                    MDTextField:
                        hint_text: "Min Temperature Limit (°C)"
                        text_color_normal: 1, 1, 1, 1
                        input_type: 'number'
                    MDTextField:
                        hint_text: "Low Water Volume Warning (L)"
                        text_color_normal: 1, 1, 1, 1
                        input_type: 'number'

                # Padding for the bottom of the scroll view
                MDBoxLayout:
                    size_hint_y: None
                    height: dp(20)
'''

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.focus_index = 0
        self.focusable_ids = []

    def on_enter(self, *args):
        """When the screen loads, initialize the focus list and draw the first yellow box."""
        # FIXED: Changed 'btn_start' to 'start_btn' to match the KV id
        self.focusable_ids = ['start_btn', 'sw_aerator', 'sw_temp', 'sw_led', 'btn_settings']
        self.draw_focus()

    def move_focus(self, step):
        """Moves the yellow focus box to the next/previous widget."""
        self.focus_index += step
        if self.focus_index >= len(self.focusable_ids):
            self.focus_index = 0
        elif self.focus_index < 0:
            self.focus_index = len(self.focusable_ids) - 1
        self.draw_focus()

    def draw_focus(self):
        """Clears old yellow boxes and draws a new one around the currently selected widget."""
        # Clear all existing focus lines
        for fid in self.focusable_ids:
            widget = self.ids[fid]
            widget.canvas.after.clear()
        
        # Draw the new bright yellow focus outline
        if self.focusable_ids:
            target_widget = self.ids[self.focusable_ids[self.focus_index]]
            with target_widget.canvas.after:
                Color(1, 1, 0, 1)  # Bright Yellow
                # Draw a rounded rectangle slightly larger than the widget itself
                Line(rounded_rectangle=(
                    target_widget.x - dp(5), 
                    target_widget.y - dp(5), 
                    target_widget.width + dp(10), 
                    target_widget.height + dp(10), 
                    dp(5)
                ), width=dp(2))

    def trigger_focused_item(self):
        """Simulates a finger tap on whatever widget currently has the yellow box."""
        if not self.focusable_ids:
            return
            
        current_id = self.focusable_ids[self.focus_index]
        widget = self.ids[current_id]
        
        if current_id == 'btn_settings':
            MDApp.get_running_app().go_to_settings()
        elif current_id.startswith('sw_'):
            # Toggle the switch visually and functionally
            widget.active = not widget.active
        # FIXED: Changed 'btn_start' to 'start_btn'
        elif current_id == 'start_btn':
            self.flash_start_button()
            MDApp.get_running_app().start_batch_count()

    def flash_start_button(self):
        """Creates a visual flash effect when triggered by physical keys."""
        btn = self.ids.start_btn
        original_color = btn.md_bg_color
        btn.md_bg_color = (0.8, 0.8, 0.8, 1)  # Flash white/light-gray
        # Revert back to deep green after 0.15 seconds
        Clock.schedule_once(lambda dt: setattr(btn, 'md_bg_color', original_color), 0.15)


class SettingsScreen(Screen):
    pass


class UlangSystemApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        
        # METHOD 1: USB Numpad/Keyboard Bindings
        # Listen for any physical keyboard/numpad presses across the entire window
        Window.bind(on_key_down=self.on_keyboard_down)
        
        return Builder.load_string(KV)

    def on_start(self):
        """Called automatically after the app builds. We set up GPIO here."""
        # METHOD 2: Physical GPIO Push Buttons
        if GPIO_AVAILABLE:
            # Map GPIO Pin 17 to go to Settings (E.g. "NEXT" button)
            self.btn_settings = HardwareButton(17)
            self.btn_settings.when_pressed = lambda: Clock.schedule_once(self.go_to_settings)

            # Map GPIO Pin 27 to go back to Dashboard (E.g. "BACK" button)
            self.btn_home = HardwareButton(27)
            self.btn_home.when_pressed = lambda: Clock.schedule_once(self.go_to_dashboard)

            # Map GPIO Pin 22 to Start the Count (E.g. "ENTER" button)
            self.btn_start = HardwareButton(22)
            self.btn_start.when_pressed = lambda: Clock.schedule_once(self.handle_physical_enter)

    # ---------------------------------------------------------
    # HARDWARE COMMAND ROUTING FUNCTIONS
    # ---------------------------------------------------------
    def on_keyboard_down(self, window, keycode, scancode, text, modifiers):
        """Routes USB Numpad/Keyboard presses to actions."""
        # Check if we are on the dashboard
        if self.root.current == "dashboard":
            dashboard = self.root.get_screen("dashboard")
            
            if keycode == 273 or keycode == 276:    # UP or LEFT Arrow
                dashboard.move_focus(-1)
            elif keycode == 274 or keycode == 275:  # DOWN or RIGHT Arrow
                dashboard.move_focus(1)
            elif keycode in [13, 271, 32]:          # ENTER or SPACE
                dashboard.trigger_focused_item()
                
        # Check if we are on the settings page
        elif self.root.current == "settings":
            if keycode == 276:  # Left arrow to act as a "Back" button
                self.go_to_dashboard()

    def handle_physical_enter(self, *args):
        """Used specifically for the GPIO button to trigger the focused item."""
        if self.root.current == "dashboard":
            dashboard = self.root.get_screen("dashboard")
            dashboard.trigger_focused_item()

    def go_to_settings(self, *args):
        if self.root.current != "settings":
            self.root.transition.direction = "left"
            self.root.current = "settings"

    def go_to_dashboard(self, *args):
        if self.root.current != "dashboard":
            self.root.transition.direction = "right"
            self.root.current = "dashboard"

    def start_batch_count(self, *args):
        """Triggered by the Touchscreen OR the Physical Buttons."""
        if self.root.current == "dashboard":
            dashboard_screen = self.root.get_screen("dashboard")
            dashboard_screen.flash_start_button()
            print("AI INITIALIZED: Starting Batch Count...")
            # Later, this is where you will tell OpenCV and YOLOv8 to start processing frames!

if __name__ == '__main__':
    UlangSystemApp().run()