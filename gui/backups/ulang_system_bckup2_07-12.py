from supabase import create_client, Client
import threading
import copy
import json # NEW: Needed to write the .json file
import os   # NEW: Needed to create folders safely

from kivy.config import Config
# Force Kivy to use the onscreen virtual keyboard for the 7-inch touchscreen
Config.set('kivy', 'keyboard_mode', 'systemandmulti')

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.animation import Animation
from kivy.properties import BooleanProperty, ColorProperty, StringProperty, NumericProperty, ObjectProperty, OptionProperty
from datetime import datetime
import random #temporary
# ---------------------------------------------------------
# HARDWARE GPIO SETUP (Fail-safe for Windows/Mac testing)
# ---------------------------------------------------------
try:
    from gpiozero import Button as HardwareButton
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: gpiozero not found. Physical GPIO buttons disabled (Running on Laptop).")

Window.size = (800, 480)

INTERFACE = '''
ScreenManager:
    DashboardScreen:
        id: dashboard_screen
    SettingsScreen:
        id: settings_screen
    LogsScreen:
        id: logs_screen
        db_client: app.db_client
# ---------------------------------------------------DASHBOARD PAGE-------------------------------------------------------
<DashboardScreen>:
    name: "dashboard"
    md_bg_color: 0, 0, 0, 1
    db_client: app.db_client 

    MDBoxLayout:
        orientation: 'vertical'
        padding: 12
        spacing: 12

        MDBoxLayout:
            size_hint_y: None
            height: 36
            spacing: 12

            MDLabel:
                text: "DASHBOARD"
                font_name: "assets/sf_txt_bold.ttf"
                font_size: 24
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                size_hint_x: None
                adaptive_width: True

            MDLabel:
                id: clock_label
                text: "--"
                font_name: "assets/sf_txt_reg.ttf"
                font_size: 24
                theme_text_color: "Custom"
                halign: "left"
                text_color: 1, 1, 1, 1

            Image:
                size_hint: None, None
                source: "res/ic_wifi.png"
                width: 26
                height: 26
                allow_stretch: True
                keep_ratio: True
                pos_hint: {"center_y": .5}
            
            Button:
                text: "Settings"
                font_name: "assets/sf_txt_reg.ttf"
                background_normal: "res/btn_pill_gray_s.png"
                background_down: "res/btn_pill_gray_s_down.png"
                size_hint_x: None
                on_release: app.go_to_settings()

            Button:
                text: "View Logs"
                font_name: "assets/sf_txt_reg.ttf"
                background_normal: "res/btn_pill_gray_s.png"
                background_down: "res/btn_pill_gray_s_down.png"
                size_hint_x: None
                width: self.texture_size[0] + 24
                on_release: app.go_to_logs()

        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: 1
            spacing: 12

            # LEFT PANE: Camera Feed
            MDCard:
                size_hint_x: 0.6
                md_bg_color: 0, 0, 0, 1
                radius: [12, 12, 12, 12]

                MDLabel:
                    text: "LIVE YOLOv8 CAMERA FEED\\n\\n[size=14][color=#666666](Awaiting OpenCV Video Stream)[/color][/size]"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.8, 0.8, 0.8, 1
                    markup: True
                    bold: True

            # RIGHT PANE: Data & Controls
            MDBoxLayout:
                orientation: 'vertical'
                size_hint: None, 1
                width: 210

                ScreenManager:
                    id: data_pane_sm
                    transition: app.get_fade_transition()

                    Screen:
                        name: 'panel_count_inactive'

                        MDCard:
                            orientation: 'vertical'
                            size_hint_y: 1
                            radius: [16]
                            padding: 12
                            spacing: 12
                            md_bg_color: 0.3, 0.3, 0.3, 1

                            MDBoxLayout:
                                orientation: 'vertical'
                                size_hint: 1, 0.2
                                #adaptive_height: True
                                valign: 'top'

                                MDLabel:
                                    text: "28.5 °C"
                                    theme_text_color: "Custom"
                                    text_color: 0.2, 0.8, 0.2, 1  # Green
                                    font_name: "assets/sf_mono_bold.otf"
                                    font_size: 32
                                    size_hint_y: None
                                    height: self.texture_size[1]

                                MDLabel:
                                    text: "WATER TEMP."
                                    theme_text_color: "Custom"
                                    text_color: 0.8, 0.8, 0.8, 1
                                    font_name: "assets/sf_txt_reg.ttf"
                                    font_size: 20
                                    size_hint_y: None
                                    height: self.texture_size[1]

                            MDBoxLayout:
                                orientation: 'vertical'
                                size_hint: 1, 0.2
                                #adaptive_height: True

                                MDLabel:
                                    text: "8.0 cm"
                                    theme_text_color: "Custom"
                                    text_color: 0.2, 0.8, 0.2, 1  # Green
                                    font_name: "assets/sf_mono_bold.otf"
                                    font_size: 32
                                    size_hint_y: None
                                    height: self.texture_size[1]

                                MDLabel:
                                    text: "WATER LEVEL"
                                    theme_text_color: "Custom"
                                    text_color: 0.8, 0.8, 0.8, 1
                                    font_name: "assets/sf_txt_reg.ttf"
                                    font_size: 20
                                    size_hint_y: None
                                    height: self.texture_size[1]

                            MDBoxLayout:
                                orientation: 'vertical'
                                size_hint: 1, 0.2
                                #adaptive_height: True

                                MDLabel:
                                    text: "2.0 L"
                                    theme_text_color: "Custom"
                                    text_color: 0.2, 0.8, 0.2, 1  # Green
                                    font_name: "assets/sf_mono_bold.otf"
                                    font_size: 32
                                    size_hint_y: None
                                    height: self.texture_size[1]

                                MDLabel:
                                    text: "WATER VOLUME"
                                    theme_text_color: "Custom"
                                    text_color: 0.8, 0.8, 0.8, 1
                                    font_name: "assets/sf_txt_reg.ttf"
                                    font_size: 20
                                    size_hint_y: None
                                    height: self.texture_size[1]

                            MDSeparator:

                            MDBoxLayout:
                                orientation: 'vertical'
                                size_hint: 1, 0.5
                                spacing: 12

                                Widget:
                                    size_hint: 1, 1

                                PillToggleButton:
                                    id: toggle_aerator
                                    size_hint: 1, None
                                    height: 64
                                    markup: True
                                    text: "[font=assets/sf_txt_bold.ttf][size=24]OPERATING[/font][/size]\\n[size=20][font=assets/sf_txt_reg.ttf]AERATOR[/font][/size]" if self.is_active else "[font=assets/sf_txt_bold.ttf][size=24]IDLE[/font][/size]\\n[size=20][font=assets/sf_txt_reg.ttf]AERATOR[/font][/size]"
                                    halign: 'center'
                                    color_on: '#0078ff'
                                    color_off: 0, 0.47, 1, 0.2
                                    line_height: 0.9

                                Widget:
                                    size_hint: 1, 1

                                PillToggleButton:
                                    id: toggle_led_panels
                                    size_hint: 1, None
                                    height: 64
                                    markup: True
                                    text: "[font=assets/sf_txt_bold.ttf][size=24]ON[/font][/size]\\n[size=20][font=assets/sf_txt_reg.ttf]LED PANELS[/font][/size]" if self.is_active else "[font=assets/sf_txt_bold.ttf][size=24]OFF[/font][/size]\\n[size=20][font=assets/sf_txt_reg.ttf]LED PANELS[/font][/size]"
                                    halign: 'center'
                                    color_on: 'ccba00'
                                    color_off: 0.8, 0.73, 0, 0.2
                                    line_height: 0.9

                                Widget:
                                    size_hint: 1, 1

                    Screen:
                        name: "panel_count_active"

                        MDCard:
                            orientation: 'vertical'
                            size_hint_y: 1
                            radius: [16]
                            padding: 12
                            spacing: 12
                            md_bg_color: 0.3, 0.3, 0.3, 1

                            ScrollView:
                                do_scroll_x: False # Force vertical scrolling only
                                size_hint: 1, 0.6

                                MDBoxLayout:
                                    id: sub_batch_scrollview
                                    orientation: 'vertical'
                                    size_hint_y: None
                                    height: self.minimum_height # CRITICAL: Allows scrolling

                            MDSeparator:

                            MDBoxLayout:
                                id: sub_batch_list
                                orientation: 'vertical'
                                size_hint: 1, 0.4

                                Widget:
                                    size_hint: 1,1

                                MDLabel:
                                    id: total_count
                                    text: str(app.total_count) if app.total_count else "--"
                                    theme_text_color: "Custom"
                                    text_color: '#0078ff'
                                    font_name: "assets/sf_mono_bold.otf"
                                    font_size: 32
                                    size_hint_y: None
                                    height: self.texture_size[1]
                                    halign: 'center'

                                MDLabel:
                                    text: "TOTAL PL COUNT"
                                    theme_text_color: "Custom"
                                    text_color: 1, 1, 1, 1
                                    font_name: "assets/sf_txt_reg.ttf"
                                    font_size: 20
                                    size_hint_y: None
                                    height: self.texture_size[1]
                                    halign: 'center'

                                Widget:
                                    size_hint: 1,1

                                Button:
                                    text: "COUNT" if app.is_counting else "+SUB-BATCH"
                                    size_hint: 1, None
                                    height: 56
                                    font_size: 24
                                    font_name: "assets/sf_txt_bold.ttf"
                                    background_normal: "res/btn_pill_blue_l.png"
                                    background_down: "res/btn_pill_blue_l_down.png"
                                    on_release:
                                        app.count_on_click()
                                
        MDBoxLayout:
            orientation: 'vertical'
            size_hint: 1, None
            height: 56
        
            ScreenManager:
                id: btm_btn_container
                transition: app.get_fade_transition()

                Screen:
                    name: 'btn_count_inactive'
        
                    Button:
                        id: start_btn
                        text: "START BATCH COUNT"
                        size_hint: 1, None
                        height: 56
                        font_size: 24
                        font_name: "assets/sf_txt_bold.ttf"
                        background_normal: "res/btn_pill_blue_l_expanded.png"
                        background_down: "res/btn_pill_blue_l_down_expanded.png"
                        on_release: 
                            app.show_entry_details()

                Screen:
                    name: 'btn_count_active'

                    MDBoxLayout:
                        orientation: 'horizontal'
                        size_hint: 1, None
                        adaptive_height: True
                        spacing: 12
        
                        Button:
                            text: "ABORT"
                            size_hint: 1, None
                            height: 56
                            font_size: 24
                            font_name: "assets/sf_txt_bold.ttf"
                            border: 28, 28, 28, 28
                            background_normal: "res/btn_pill_red_l.png"
                            background_down: "res/btn_pill_red_l_down.png"
                            on_release:
                                app.deactivate_count(abort=True)

                        Button:
                            text: "FINISH"
                            size_hint: 1, None
                            height: 56
                            font_size: 24
                            font_name: "assets/sf_txt_bold.ttf"
                            border: 28, 28, 28, 28
                            background_normal: "res/btn_pill_green_l.png"
                            background_down: "res/btn_pill_green_l_down.png"
                            on_release:
                                app.finish_count()
# --------------------------------------------------SETTINGS PAGE-------------------------------------------------------
<SettingsScreen>:
    name: "settings"
    md_bg_color: 0.08, 0.08, 0.08, 1

    MDBoxLayout:
        orientation: 'vertical'
        size_hint_y: 1
        padding: 12
        spacing: 12

        MDBoxLayout:
            size_hint: 1, None
            height: 36
            spacing: 12

            Button:
                id: btn_bck_dashboard
                text: "Dashboard"
                font_name: "assets/sf_txt_reg.ttf"
                background_normal: "res/btn_pill_gray_s.png"
                background_down: "res/btn_pill_gray_s_down.png"
                size_hint_x: None
                width: self.texture_size[0] + 24
                height: self.texture_size[1]
                on_release: 
                    app.go_to_dashboard()

            MDLabel:
                text: "Settings"
                halign: 'center'
                font_name: "assets/sf_txt_bold.ttf"
                font_size: 24
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                size_hint_x: 1

            Widget:
                size_hint_x: None
                width: root.ids.btn_bck_dashboard.width - 26

            Image:
                size_hint: None, None
                source: "res/ic_wifi.png"
                width: 26
                height: 26
                allow_stretch: True
                keep_ratio: 
                pos_hint: {"center_y": .5}

        ScrollView:
            do_scroll_x: False # Force vertical scrolling only
            size_hint: 1, 1

            MDBoxLayout:
                id: sub_batch_scrollview
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height # CRITICAL: Allows scrolling
                spacing: 12

                MDCard:
                    orientation: 'horizontal'
                    size_hint: 1, None
                    height: 64
                    padding: 12
                    spacing: 12

                    MDLabel:
                        text: "Wi-Fi"
                        halign: 'left'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        size_hint_x: 1

                    MDLabel:
                        text: "Connected to SSID"
                        halign: 'right'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 0.5
                        size_hint_x: 1

                MDCard:
                    orientation: 'horizontal'
                    size_hint: 1, None
                    height: 64
                    padding: [19, 0, 19, 0]
                    spacing: 12

                    MDLabel:
                        text: "Screen Brightness"
                        halign: 'left'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        size_hint_x: 0.3

                    Slider:
                        min: 0
                        max: 100
                        value: 60
                        step: 20
                        size_hint_x: 0.7
                        value_track: True
                        value_track_color: '#ffff00'
                        cursor_size: 64, 34
                        cursor_image: 'res/slider_cursor.png'
                        background_width: 0

                        canvas.before:
                            Color:
                                rgba: 0.25, 0.25, 0.25, 1  # Your custom empty color (Dark Gray)
                            Line:
                                # THE MATH TRAP: Kivy Line width is a radius (half the thickness).
                                # To match the 18dp value_track_width, this must be 9dp!
                                width: 4 
                                cap: 'round'
                                
                                # Draw the line exactly from the left padding to the right padding
                                points: [self.x + self.padding, self.center_y, self.right - self.padding, self.center_y]

                MDCard:
                    orientation: 'vertical'
                    size_hint: 1, None
                    height: self.minimum_height
                    padding: [19, 0, 19, 0]

                    MDLabel:
                        text: "Sync Logs to Cloud"
                        halign: 'left'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: '#008ade'
                        size_hint: 1, None
                        height: 64

                    MDSeparator:

                    MDLabel:
                        text: "Export Logs"
                        halign: 'left'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: '#008ade'
                        size_hint: 1, None
                        height: 64

                    MDSeparator:

                    MDLabel:
                        text: "Clear Locally Stored Logs"
                        halign: 'left'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: 'db3838'
                        size_hint: 1, None
                        height: 64

# --------------------------------------------------LOGS PAGE-------------------------------------------------------
<LogsScreen>:
    name: "logs"
    md_bg_color: 0.08, 0.08, 0.08, 1

    MDBoxLayout:
        orientation: 'vertical'
        size_hint_y: 1
        padding: 12
        spacing: 12

        MDBoxLayout:
            size_hint: 1, None
            height: 36
            spacing: 12

            Button:
                id: logs_btn_bck_dashboard
                text: "Dashboard"
                font_name: "assets/sf_txt_reg.ttf"
                background_normal: "res/btn_pill_gray_s.png"
                background_down: "res/btn_pill_gray_s_down.png"
                size_hint_x: None
                width: self.texture_size[0] + 24
                height: self.texture_size[1]
                on_release: 
                    app.go_to_dashboard()

            MDLabel:
                text: "Logs"
                halign: 'center'
                font_name: "assets/sf_txt_bold.ttf"
                font_size: 24
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                size_hint_x: 1

            Widget:
                size_hint_x: None
                width: root.ids.logs_btn_bck_dashboard.width - 26

            Image:
                size_hint: None, None
                source: "res/ic_wifi.png"
                width: 26
                height: 26
                allow_stretch: True
                keep_ratio: 
                pos_hint: {"center_y": .5}

            Button:
                id: logs_btn_bck_dashboard
                text: "Sync Logs"
                font_name: "assets/sf_txt_reg.ttf"
                background_normal: "res/btn_pill_gray_s.png"
                background_down: "res/btn_pill_gray_s_down.png"
                size_hint_x: None
                width: self.texture_size[0] + 24
                height: self.texture_size[1]

        RecycleView:
            id: logs_recycle_view
            viewclass: 'BatchLogItem' # <--- Points directly to your custom MDCard!
            
            # This layout manager handles the scrolling math
            RecycleBoxLayout:
                default_size: None, 215 # Approximate starting height of your card
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'
                spacing: dp(15)
                padding: dp(20)
# --------------------------------------------------CUSTOM CLASSES-------------------------------------------------------
<Snackbar>:
    id: snackbar
    size_hint: None, None
    size: dp(350), 48
    opacity: 0
    pos_hint: {"center_x": 0.5, "center_y": 0.05} 
    padding: 14
    elevation: 3
    shadow_color: 0, 0, 0, 0.1
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1 
            
        BorderImage:
            pos: self.pos
            size: self.size
            source: 'res/bg_snackbar_red.png' if root.warning_mode else 'res/bg_snackbar_white.png'
            border: [24, 24, 24, 24]
    
    MDLabel:
        id: toast_text
        text: ""
        font_name: 'assets/sf_txt_reg.ttf'
        font_size: 20
        theme_text_color: "Custom"
        text_color: (1, 1, 1, 1) if root.warning_mode else (0, 0, 0, 1)
        halign: 'center'

<BatchCountDialog@Popup>
    width: 500
    height: 350
    size_hint: None, None
    background: ''
    background_color: 0, 0, 0, 0
    separator_height: 0
    title: ""
    auto_dismiss: False

    MDBoxLayout:
        orientation: 'vertical'
        size_hint: 1, None
        height: 350
        spacing: 28
        padding: 12

        canvas.before:
            Color:
                rgba: 1, 1, 1, 1 # Ensure the image renders at full brightness
            BorderImage:
                source: 'res/bg_dialog.png'
                pos: self.pos
                size: self.size
                border: [35, 35, 35, 35]

        MDBoxLayout:
            orientation: 'vertical'
            size_hint: 1, None
            spacing: 8
            padding: 15

            MDLabel:
                text: "Batch Count Details"
                font_name: "assets/sf_txt_bold.ttf"
                font_size: 24
                text_color: 1, 1, 1, 1
                size_hint_x: 1
                halign: 'left'

            MDLabel:
                text: "Please provide the following details before you start counting."
                font_name: "assets/sf_txt_reg.ttf"
                font_size: 20
                text_color: 1, 1, 1, 1
                size_hint_x: 1
                halign: 'left'

        MDBoxLayout:
            orientation: 'vertical'
            size_hint: 1, None
            height: 108
            spacing: 12

            TextInput:
                id: input_name_batch
                hint_text: "Enter Batch Name or ID"
                multiline: False
                size_hint_y: None
                height: 48
                padding: ["16dp", 10, "16dp", 8]
                background_normal: 'res/bg_txt_field_inactive.png'
                background_active: 'res/bg_txt_field_active.png'
                border: [1, 1, 1,1]  
                font_name: "assets/sf_txt_reg.ttf"
                font_size: 24
                foreground_color: 1, 1, 1, 1

            TextInput:
                id: input_name_op
                hint_text: "Enter Operator's Name"
                multiline: False
                size_hint_y: None
                height: 48
                padding: ["16dp", 10, "16dp", 8]
                background_normal: 'res/bg_txt_field_inactive.png'
                background_active: 'res/bg_txt_field_active.png'
                border: [1, 1, 1,1]  
                font_name: "assets/sf_txt_reg.ttf"
                font_size: 24
                foreground_color: 1, 1, 1, 1

        MDBoxLayout:
            orientation: 'horizontal'
            size_hint: 1, None
            spacing: 12
            height: 64

            Button:
                text: "CANCEL"
                size_hint: 1, None
                height: 56
                font_size: 24
                font_name: "assets/sf_txt_bold.ttf"
                background_normal: "res/btn_pill_gray_l.png"
                background_down: "res/btn_pill_gray_l_down.png"
                on_release:
                    root.dismiss()

            Button:
                text: "PROCEED"
                size_hint: 1, None
                height: 56
                font_size: 24
                font_name: "assets/sf_txt_bold.ttf"
                background_normal: "res/btn_pill_blue_l.png"
                background_down: "res/btn_pill_blue_l_down.png"
                on_release: 
                    app.activate_count(input_name_batch = root.ids.input_name_batch.text, input_name_op = root.ids.input_name_op.text)

<SystemDialog>
    width: 500
    height: dialog_container.height
    size_hint: None, None
    background: ''
    background_color: 0, 0, 0, 0
    separator_height: 0
    title: ""

    MDBoxLayout:
        id: dialog_container
        orientation: "vertical"
        size_hint: 1, None
        height: 215
        padding: 12

        canvas.before:
            Color:
                rgba: 1, 1, 1, 1 # Ensure the image renders at full brightness
            BorderImage:
                source: 'res/bg_dialog.png'
                pos: self.pos
                size: self.size
                border: [35, 35, 35, 35]

        MDBoxLayout:
            orientation: 'vertical'
            size_hint: 1, 1
            spacing: 19

            MDBoxLayout:
                orientation: 'vertical'
                size_hint: 1, 1
                spacing: 8
                padding: 15

                MDLabel:
                    text: root.dialog_title
                    font_name: "assets/sf_txt_bold.ttf"
                    font_size: 24
                    text_color: 1, 1, 1, 1
                    size_hint_x: 1
                    height: self.texture_size[1]
                    halign: 'left'

                MDLabel:
                    text: root.dialog_msg
                    font_name: "assets/sf_txt_reg.ttf"
                    font_size: 20
                    text_color: 1, 1, 1, 1
                    size_hint_x: 1
                    height: self.texture_size[1]
                    halign: 'left'

            MDBoxLayout:
                orientation: 'horizontal'
                size_hint: 1, None
                spacing: 12
                height: 56

                Button:
                    text: "CANCEL"
                    size_hint: 1, None
                    height: 56
                    font_size: 24
                    font_name: "assets/sf_txt_bold.ttf"
                    background_normal: "res/btn_pill_gray_l.png"
                    background_down: "res/btn_pill_gray_l_down.png"
                    on_release:
                        root.dismiss()

                Button:
                    text: "PROCEED"
                    size_hint: 1, None
                    height: 56
                    font_size: 24
                    font_name: "assets/sf_txt_bold.ttf"
                    background_normal: "res/btn_pill_green_l.png" if root.mode == "normal" else "res/btn_pill_red_l.png"
                    background_down: "res/btn_pill_green_l_down.png" if root.mode == "normal" else  "res/btn_pill_red_l_down.png"
                    on_release: 
                        root.execute_proceed()

<PillToggleButton>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    background_down: ''
    color: 1, 1, 1, 1
    canvas.before:
        Color:
            rgba: self.color_pressed if self.state == 'down' else self.current_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.height / 2]

<BatchLogItem>
    orientation: 'vertical'
    padding: 19
    size_hint: 1, None
    height: 230
    radius: [16, 16, 16, 16]
    spacing: 8

    MDBoxLayout:
        orientation: 'horizontal'
        size_hint_x: 1
        size_hint_y: None

        MDLabel:
            markup: True
            size_hint_x: 1
            size_hint_y: None
            height: self.texture_size[1]
            font_size: 24
            halign: 'left'
            text: f"[font=assets/sf_mono_bold.otf][color=#ffffff]BATCH ID: [/font][/color][font=assets/sf_mono_bold.otf][color=#ffffff]{root.log_id_batch}[/font][/color]"

        MDLabel:
            size_hint_x: 1
            size_hint_y: None
            height: self.texture_size[1]
            font_size: 24
            font_name: 'assets/sf_mono_reg.otf'
            text_color: 1, 1, 1, 0.5
            text: root.log_timestamp
            halign: 'right'
    
    MDLabel:
        markup: True
        size_hint_x: 1
        size_hint_y: None
        height: self.texture_size[1]
        font_size: 24
        halign: 'left'
        text: f"[font=assets/sf_mono_reg.otf][color=#ffffff]OPERATOR: [/font][/color][font=assets/sf_mono_reg.otf][color=#008ade]{root.log_name_op}[/font][/color]"

    MDLabel:
        markup: True
        size_hint_x: 1
        size_hint_y: None
        height: self.texture_size[1]
        font_size: 24
        halign: 'left'
        text: f"[font=assets/sf_mono_reg.otf][color=#ffffff]PL COUNT: [/font][/color][font=assets/sf_mono_reg.otf][color=#008ade]{root.log_pl_count}[/font][/color]"

    MDLabel:
        markup: True
        size_hint_x: 1
        size_hint_y: None
        height: self.texture_size[1]
        font_size: 24
        halign: 'left'
        text: f"[font=assets/sf_mono_reg.otf][color=#ffffff]SUB-BATCHES: [/font][/color][font=assets/sf_mono_reg.otf][color=#008ade]{root.log_num_sbatches}[/font][/color]"    

    MDLabel:
        markup:True
        size_hint_x: 1
        size_hint_y: None
        height: self.texture_size[1]
        font_size: 24
        halign: 'left'
        text: f"[font=assets/sf_mono_reg.otf][color=#ffffff]MARGIN OF ERROR: [/font][/color][font=assets/sf_mono_reg.otf][color=#008ade]{root.log_margin_of_err:.2f}[/font][/color]"

<SubBatchItem>
    orientation: "vertical"
    size_hint: 1, None
    height: 64
    radius: [4, 4, 4, 4]
    md_bg_color: (1, 1, 1, 1) if root.is_active else (0, 0, 0, 0)
                    
    MDBoxLayout:
        size_hint: 1, None
        orientation: "horizontal"

        MDBoxLayout:
            size_hint: 1, None
            orientation: "vertical"
            spacing: 3
            padding: 8

            MDLabel:
                text: root.batch_name
                theme_text_color: "Custom"
                text_color: (0,0,0,1) if root.is_active else (1, 1, 1, 1)
                font_name: "assets/sf_txt_reg.ttf"
                font_size: 14
                size_hint: 1, None
                height: self.texture_size[1]
                halign: 'left'

            MDLabel:
                text: str(root.count) if not root.count == -1 else "--"
                theme_text_color: "Custom"
                text_color: "#0078ff"
                font_name: "assets/sf_mono_bold.otf"
                font_size: 20
                size_hint: 1, None
                height: self.texture_size[1]
                halign: 'left'
                    
        MDIconButton:
            icon: "res/ic_erase_itm_s.png"
            theme_text_color: "Custom"
            on_release: app.remove_sub_batch(root)
            height: 16
            width: 16

    MDSeparator:
'''

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.focus_index = 0
        self.focusable_ids = []
        Clock.schedule_interval(self.update_clock, 1)

    def update_clock(self, *args):
        """Fetches and formats the current time, updating the UI label."""
        now = datetime.now()
        month = now.strftime('%b').upper()
        time_str = now.strftime('%I:%M %p').lstrip('0') 
        formatted_time = f"{month} {now.day}, {now.year} | {time_str}"
        
        if 'clock_label' in self.ids:
            self.ids.clock_label.text = formatted_time

class SettingsScreen(Screen):
    pass

class LogsScreen(Screen):
    db_client = ObjectProperty(None, allownone=True)
    def on_enter(self):
        # Start the loading spinner here if you have one
        threading.Thread(target=self.fetch_and_merge_logs).start()

    def fetch_and_merge_logs(self):
        master_log_list = []

        # LOAD LOCAL "PENDING" LOGS
        pending_folder = "pending_sync"
        if os.path.exists(pending_folder):
            for filename in os.listdir(pending_folder):
                if filename.endswith(".json"):
                    filepath = os.path.join(pending_folder, filename)
                    try:
                        with open(filepath, "r") as f:
                            log_data = json.load(f)
                            # Add a custom UI flag so the operator knows it isn't in the cloud yet
                            log_data["ui_sync_status"] = "Pending (Offline)" 
                            master_log_list.append(log_data)
                    except Exception as e:
                        print(f"Error reading local log {filename}: {e}")

        #LOAD CLOUD (OR LOCAL HISTORY) LOGS
        try:
            response = self.db_client.table("batch_count_history_logs").select("*").order("timestamp", desc=True).limit(50).execute()
            
            for cloud_log in response.data:
                cloud_log["ui_sync_status"] = "Synced to Cloud"
                master_log_list.append(cloud_log)
                
        except Exception as e:
            print(f"Offline Mode Active. Could not reach Supabase: {e}")
            # FALLBACK: If you implement a 'synced_history' local folder, 
            # you would run a loop similar to Step 1 right here!

        # SORT THE MERGED LIST BY TIMESTAMP
        try:
            master_log_list.sort(
                key=lambda x: datetime.strptime(x["timestamp"], "%b %d, %Y %I:%M %p"), 
                reverse=True
            )
        except Exception as e:
            print(f"Sorting error (likely a timestamp format mismatch): {e}")

        #FORMAT FOR RECYCLEVIEW & UPDATE UI
        rv_data = []
        for log in master_log_list:
            # Map the database keys to the variables expected by your KV viewclass
            rv_data.append({
                "log_id_batch": str(log.get("batch_id", "UNKNOWN")),
                "log_timestamp": str(log.get("timestamp", "No Date")),
                "log_name_op": str(log.get("op_name", "Unknown Operator")),
                "log_pl_count": int(log.get("total_pl_count", 0)),
                "log_num_sbatches": int(log.get("num_of_sbatch", 0)),
                "log_margin_of_err": float(log.get("accuracy", 0.0))
            })

        # Safely teleport the data back to the Kivy Main Thread
        Clock.schedule_once(lambda dt: self.update_rv(rv_data))

    def update_rv(self, formatted_data):
        # Stop loading spinner here
        # Inject data into the RecycleView
        self.ids.logs_recycle_view.data = formatted_data

class UlangSystemApp(MDApp):
#===STATUS
    count_active = BooleanProperty(False)
    is_counting = BooleanProperty(False)
    is_online = BooleanProperty(False)
#===PLACEHOLDERS
    dialog = None
    sub_batch_history = {}
    payload = {
        "timestamp": None,
        "batch_id": None,
        "op_name": None,
        "total_pl_count": None,
        "num_of_sbatch": None,
        "counts_of_sbatch": None,
        "model_version": None,
        "accuracy": None
    }
    name_count_batch = ""
    name_operator = ""
    total_batches_created = NumericProperty(0)
    total_count = NumericProperty(0)
    current_active_widget = ObjectProperty(None, allownone=True)
    snackbar = None
    empty_chamber = True
#===CLIENT CREATION
    SUPABASE_API_URL = 'https://nltmvrjxasslpqbdyamg.supabase.co'
    SUPABASE_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5sdG12cmp4YXNzbHBxYmR5YW1nIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM2MjcwNzUsImV4cCI6MjA5OTIwMzA3NX0.LCwGdbW5DVKSjl8Qql65LjQQgjOYMkhre7y3q94Eo68'

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        try:
            self.db_client: Client = create_client(self.SUPABASE_API_URL, self.SUPABASE_API_KEY)
            self.is_online = True
            print("Successfully connected to Supabase Cloud!")
        except Exception as e:
            self.is_online = False
            print(f"WARNING: Cloud connection failed. Running offline. Error: {e}")
        # METHOD 1: USB Numpad/Keyboard Bindings
        # Listen for any physical keyboard/numpad presses across the entire window
        Window.bind(on_key_down=self.on_keyboard_down)
        return Builder.load_string(INTERFACE)

    def get_fade_transition(self):
        return FadeTransition(duration=0.1)

    def on_start(self):
        """Called automatically after the app builds. We set up GPIO here."""
        self.right_pane = self.root.ids.dashboard_screen.ids.data_pane_sm
        self.right_pane.current = "panel_count_inactive"
        self.btm_btn = self.root.ids.dashboard_screen.ids.btm_btn_container
        self.btm_btn.current = "btn_count_inactive"
        self.aerator = self.root.ids.dashboard_screen.ids.toggle_aerator
        self.led_panels = self.root.ids.dashboard_screen.ids.toggle_led_panels
        self.sub_batch_scrollview = self.root.ids.dashboard_screen.ids.sub_batch_scrollview
        # METHOD 2: Physical GPIO Push Buttons
        if GPIO_AVAILABLE:
            # Map GPIO Pin 17 to go to Settings (E.g. "NEXT" button)
            self.btn_settings = HardwareButton(17)
            self.btn_settings.when_pressed = lambda: Clock.schedule_once(self.go_to_settings)

            # Map GPIO Pin 27 to go back to Dashboard (E.g. "BACK" button)
            self.btn_home = HardwareButton(27)
            self.btn_home.when_pressed = lambda: Clock.schedule_once(self.hboard)

            # Map GPIO Pin 22 to Start the Count (E.g. "ENTER" button)
            self.btn_start = HardwareButton(22)
            self.btn_start.when_pressed = lambda: Clock.schedule_once(self.start_batch_count)

    def on_keyboard_down(self, window, keycode, scancode, text, modifiers):
        """Routes USB Numpad/Keyboard presses to actions."""
        # Keycode 275 = Right Arrow
        if keycode == 275:
            self.go_to_settings()
        # Keycode 276 = Left Arrow
        elif keycode == 276:
            self.go_to_dashboard()
        # Keycode 13 = Standard Enter, Keycode 271 = Numpad Enter
        elif keycode in [13, 271]:
            self.start_batch_count()
#==================================================SCREEN NAVIGATION FUNCTIONS===============================================
    def go_to_settings(self, *args):
        if self.root.current != "settings":
            self.root.transition.direction = "left"
            self.root.current = "settings"

    def go_to_logs(self, *args):
        if self.root.current != "logs":
            self.root.transition.direction = "left"
            self.root.current = "logs"

    def go_to_dashboard(self, *args):
        if self.root.current != "dashboard":
            self.root.transition.direction = "right"
            self.root.current = "dashboard"

    def start_batch_count(self, *args):
        """Triggered by the Touchscreen OR the Physical Buttons."""
        if self.root.current == "dashboard":
            dashboard_screen = self.root.get_screen("dashboard")
            print("AI INITIALIZED: Starting Batch Count...")
            # Later, this is where you will tell OpenCV and YOLOv8 to start processing frames!

    def show_entry_details(self, *args):
        self.popup = Factory.BatchCountDialog()
        self.popup.open()

    def process_wifi_connection(self, *args):
        ssid = self.dialog.content_cls.ids.ssid_input.text
        password = self.dialog.content_cls.ids.password_input.text
        print(f"Hatchery Tech entered -> SSID: {ssid}, Password: {password}")
        self.dialog.dismiss()

    def activate_count(self, input_name_batch = "", input_name_op = "", *args):
        self.name_count_batch = input_name_batch
        self.name_operator = input_name_op
    
        def execute_activation():
            self.count_active = True
            print('Counting Process Activated')
            self.popup.dismiss()
            self.aerator.is_active = False
            self.aerator.is_toggleable = False
            self.led_panels.is_active = True
            self.led_panels.is_toggleable = False
            self.right_pane.current = "panel_count_active"
            self.btm_btn.current = "btn_count_active"
            print(f"Count started for: {self.name_count_batch}.\nOperated by: {self.name_operator}")

        if not (self.name_count_batch and self.name_operator):
            self.show_snackbar(warning_mode=True, message="Batch detail entries are required.")
        else:
            execute_activation()

    def deactivate_count(self, abort = False, *args):
        def execute_deactivation():
            self.count_active = False
            print('Counting Process Deactivated')
#-----------Reset Status
            self.aerator.is_toggleable = True
            self.led_panels.is_toggleable = True
#-----------Reset Containers
            self.right_pane.current = "panel_count_inactive"
            self.btm_btn.current = "btn_count_inactive"
            self.sub_batch_scrollview.clear_widgets()
#-----------Clear Placeholders and Payload
            self.sub_batch_history.clear()
            self.total_count = 0
            self.name_count_batch = ""
            self.name_operator = ""
            self.payload.update({
                "timestamp": None,
                "batch_id": None,
                "op_name": None,
                "total_pl_count": None,
                "num_of_sbatch": None,
                "counts_of_sbatch": None,
                "model_version": "",
                "accuracy": float(0)
            })

        if self.sub_batch_history and abort:
            dialog = SystemDialog(
                dialog_title = "Abort Batch Count",
                dialog_msg = "Are you sure you want to abort the batch count process? This process will discard your progress and cannot be undone.",
                mode = 'destructive',
                command_on_proceed = execute_deactivation
            )
            dialog.open()
        else: 
            execute_deactivation()

    def finish_count(self):
        def execute_finish():
            self.save_batch_log()
            self.deactivate_count()

        dialog = SystemDialog(
                dialog_title = "Save Results",
                dialog_msg = "Proceed with saving results?",
                mode = 'normal',
                command_on_proceed = execute_finish
            )
        dialog.open()

    def show_snackbar(self, message = "", warning_mode = False, *args):
        if not self.snackbar:
            self.snackbar = Snackbar(warning_mode = warning_mode)
        if self.snackbar.parent:
            self.snackbar.parent.remove_widget(self.snackbar)
        Window.add_widget(self.snackbar)
        self.snackbar.ids.toast_text.text = message
        Animation.cancel_all(self.snackbar)
        anim_in = Animation(
            opacity=1, 
            pos_hint={"center_x": 0.5, "center_y": 0.10}, 
            duration=0.2, 
            t="out_quad"
        )
        anim_in.start(self.snackbar)
        Clock.schedule_once(self.hide_snackbar, 3)

    def hide_snackbar(self, dt=None):
        if not self.snackbar:
            return
        anim_out = Animation(
            opacity=0, 
            pos_hint={"center_x": 0.5, "center_y": 0.05}, 
            duration=0.3, 
            t="in_quad"
        )

#-------Completely remove it from the Window memory when done
        anim_out.bind(on_complete=lambda *args: Window.remove_widget(self.snackbar))
        anim_out.bind(on_complete=lambda *args: Window.remove_widget(self.snackbar))
        anim_out.start(self.snackbar)

    def count_on_click(self):
        if not self.is_counting:
#===========STATE 1: ADDING A SUB-BATCH
            self.is_counting = True
#-----------Increment the absolute counter
            self.total_batches_created += 1
            new_name = f"SUB-BATCH {self.total_batches_created}"
            
            new_widget = SubBatchItem(
                batch_name=new_name,
                is_active=True
            )
            
#-----------Add to UI and Backend Data
            self.sub_batch_scrollview.add_widget(new_widget)
            self.sub_batch_history[new_name] = -1 
            self.current_active_widget = new_widget
            
        else:
#===========STATE 2: EXECUTING THE COUNT
            self.is_counting = False
            simulated_count = random.randint(40, 300) #replace by inferred instances of pl 
#-----------Update UI Widget
            self.current_active_widget.count = simulated_count
            self.current_active_widget.is_active = False
#-----------Update Backend Data
            self.total_count += simulated_count
            self.sub_batch_history[self.current_active_widget.batch_name] = simulated_count
            self.current_active_widget = None

    def remove_sub_batch(self, widget_to_remove):
#-------If we are deleting the active widget, reset the system state
        def execute_deletion():
            if widget_to_remove.is_active:
                self.is_counting = False
                self.current_active_widget = None
            if widget_to_remove.count > 0:
                self.total_count -= widget_to_remove.count
            if widget_to_remove.batch_name in self.sub_batch_history:
                del self.sub_batch_history[widget_to_remove.batch_name]
            self.sub_batch_scrollview.remove_widget(widget_to_remove)
            print(f"Removed {widget_to_remove.batch_name}. Current Backend Data:", self.sub_batch_history)
#-------Show a confirmation dialog
        dialog = SystemDialog(
            dialog_title = "Remove Sub-batch",
            dialog_msg = "Are you sure you want to remove this Sub-batch? This process cannot be undone.", 
            mode = "destructive", 
            command_on_proceed = execute_deletion)
        dialog.open()

    def show_sys_dialog(self, title = "", msg = "", mode = "normal", cmd = None, **kwargs):
        dialog = SystemDialog(
            dialog_title = title,
            dialog_msg = msg,
            mode = mode,
            command_on_proceed = cmd
        )
        dialog.open()

    def function_test(self):
        print("Congrats it works")
#=======================================================Database Functions=============================================================
    def save_batch_log(self):
        self.payload.update({
            "timestamp": datetime.now().strftime("%b %d, %Y %I:%M %p"),
            "batch_id": self.name_count_batch,
            "op_name": self.name_operator,
            "total_pl_count": self.total_count,
            "num_of_sbatch": len(self.sub_batch_history),
            "counts_of_sbatch": self.sub_batch_history,
            "model_version": "ulang-obb-v2",
            "accuracy": float(0)
        })
        cached_payload = copy.deepcopy(self.payload)

        def push_data():
            try:
                self.db_client.table("batch_count_history_logs").insert(cached_payload).execute()
                print("Log Saved to Database:")

                for key, value in cached_payload.items():
                    print(f"{key}: {value} | type: {type(value)}")

                Clock.schedule_once(lambda dt: self.show_snackbar(warning_mode = False, message=f"{cached_payload["batch_id"]} is saved to Logs"))

            except Exception as e:
                err = e
                Clock.schedule_once(lambda dt: self.show_snackbar(warning_mode=True, message=f"Failed to push batch log to database: {e}"))

        def save_to_local():
            try:
                folder_name = "pending_sync"
                os.makedirs(folder_name, exist_ok=True) 

                safe_batch_name = str(cached_payload["batch_id"]).replace(" ", "_")
                filename = f"BCH{datetime.now().strftime("%Y%d%m%H%M-%f")}.json"
                filepath = os.path.join(folder_name, filename)

                with open(filepath, "w") as json_file:
                    json.dump(cached_payload, json_file, indent=4) 
                
                self.show_snackbar(warning_mode=True, message="System offline, log saved locally.")
                print(f"Success: Local Backup created at {filepath}")
                
            except Exception as e:
                print(f"CRITICAL HARDWARE ERROR: Failed to save local file! {e}")

        if self.is_online:
            threading.Thread(target=push_data).start()
        else:    
            save_to_local()

    def fetch_db(self):
        pass

    def sync_db(self):
        pass

class PillToggleButton(Button):
    is_toggleable = BooleanProperty(True)
    is_active = BooleanProperty(False)

    color_on = ColorProperty([0.1, 0.6, 0.2, 1])
    color_off = ColorProperty([0.25, 0.25, 0.25, 1])
    color_pressed = ColorProperty([0.4, 0.4, 0.4, 1])

    current_color = ColorProperty([0.25, 0.25, 0.25, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color_on = self.color_on
        self.color_off = self.color_off
        self.current_color = self.color_on if self.is_active else self.color_off

    def on_release(self, *args):
        super().on_release(*args)

        if self.is_toggleable:
            self.is_active = not self.is_active
        else:
            print(f"[{self.text}] Standard Push Triggered!")

    def on_is_active(self, instance, value):
        if value:
            self.current_color = self.color_on
        else:
            self.current_color = self.color_off

class SubBatchItem(MDBoxLayout):
    batch_name = StringProperty("")
    count = NumericProperty(-1)
    is_active = BooleanProperty(False)

class SystemDialog(Popup):
    dialog_title = StringProperty("Title")
    dialog_msg = StringProperty("Dialog Message.")
    mode = OptionProperty("normal", options=["normal", "destructive"])
    command_on_proceed = ObjectProperty(None, allownone=True)

    def execute_proceed(self):
        print("execute_proceed is called")
        if self.command_on_proceed and callable(self.command_on_proceed): 
            self.command_on_proceed()
        self.dismiss()

class Snackbar(MDBoxLayout):
    warning_mode = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.warning_mode = self.warning_mode

class BatchLogItem(MDCard):
    log_timestamp = StringProperty("")
    log_id_batch = StringProperty("")
    log_name_op = StringProperty("")
    log_pl_count = NumericProperty(0)
    log_num_sbatches = NumericProperty(0)
    log_margin_of_err = NumericProperty(0.0)

if __name__ == '__main__':
    UlangSystemApp().run()