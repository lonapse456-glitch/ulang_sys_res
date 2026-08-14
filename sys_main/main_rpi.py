from supabase import create_client, Client
import threading
import copy
import json
import os
import uuid
import subprocess
import glob
import time

import serial

import traceback

import cv2

from ultralytics import YOLO

from kivy.config import Config

Config.set('kivy', 'keyboard_mode', 'systemandmulti')
Config.set('graphics', 'fullscreen', 'auto')
Config.set('graphics', 'resizable', False)

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy.factory import Factory
from kivy.graphics.texture import Texture
from kivy.properties import BooleanProperty, ColorProperty, StringProperty, NumericProperty, ObjectProperty, OptionProperty
from kivymd.uix.screen import MDScreen
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.animation import Animation
from datetime import datetime
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
import random #temporary
# ---------------------------------------------------------
# HARDWARE GPIO SETUP (Fail-safe for Windows/Mac testing)
# ---------------------------------------------------------

from picamera2 import Picamera2, Preview
from libcamera import controls

'''try:
    from gpiozero import Button as HardwareButton
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: gpiozero not found. Physical GPIO buttons disabled (Running on Laptop).")'''
GPIO_AVAILABLE=False
Window.size = (800, 480)

try:
    arduino = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    time.sleep(2) # Give the Arduino a second to reset after connecting
except Exception as e:
    print(f"Error connecting to Arduino: {e}")

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

    MDBoxLayout:
        orientation: 'vertical'
        padding: 12
        spacing: 12

        MDBoxLayout:
            size_hiny_x: 1
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
                width: 26
                height: 26
                source: f"res/ic_wifi_{app.wifi_stat[app.wifi_strength]}.png"
                allow_stretch: True
                keep_ratio: True
                pos_hint: {"center_y": .5}
            
            Button:
                text: "Settings"
                font_name: "assets/sf_txt_reg.ttf"
                font_size: 18
                background_normal: "res/btn_pill_gray_s.png"
                background_down: "res/btn_pill_gray_s_down.png"
                size_hint_x: None
                on_release: app.go_to_settings()

            Button:
                text: "View Logs"
                font_name: "assets/sf_txt_reg.ttf"
                font_size: 18
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

                ScreenManager:
                    id: camfeed_pane
                    transition: app.get_fade_transition()
                    
                    MDScreen:
                        name: "camfeed_loading_screen"

                        MDBoxLayout:
                            orientation: 'vertical'
                            adaptive_height: True
                            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                            spacing: 16
                            
                            MDSpinner:
                                size_hint: None, None
                                size: dp(26), dp(26)
                                pos_hint: {'center_x': .5}
                                active: True
                                
                            MDLabel:
                                text: "Camera Loading..."
                                font_name: "assets/sf_txt_reg.ttf"
                                font_size: 24
                                halign: "center"
                                theme_text_color: "Secondary"
                                adaptive_height: True

                    MDScreen:
                        name: "camfeed_live_screen"

                        Image:
                            id: camera_feed
                            size_hint: 1, 1
                            allow_stretch: True
                            keep_ratio: True

                    MDScreen: 
                        name: "camfeed_null_screen"

                        MDLabel:
                            text: "Empty Chamber Detected"
                            halign: "center"
                    
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
                                size_hint: 1, 0.18
                                valign: 'bottom'

                                MDLabel:
                                    id: water_temp_label
                                    text: "28.5 °C"
                                    theme_text_color: "Custom"
                                    text_color: 0.2, 0.8, 0.2, 1 
                                    font_name: "assets/sf_mono_bold.otf"
                                    font_size: 30
                                    size_hint_y: None
                                    height: self.texture_size[1]

                                MDLabel:
                                    text: "WATER TEMP."
                                    theme_text_color: "Custom"
                                    text_color: 0.8, 0.8, 0.8, 1
                                    font_name: "assets/sf_txt_reg.ttf"
                                    font_size: 18
                                    size_hint_y: None
                                    valign: 'top'
                                    height: self.texture_size[1]

                            MDBoxLayout:
                                orientation: 'vertical'
                                size_hint: 1, 0.18
                                #adaptive_height: True

                                MDLabel:
                                    id: water_lvl_label
                                    text: "8.0 cm"
                                    theme_text_color: "Custom"
                                    text_color: 0.2, 0.8, 0.2, 1  # Green
                                    font_name: "assets/sf_mono_bold.otf"
                                    font_size: 30
                                    size_hint_y: None
                                    height: self.texture_size[1]

                                MDLabel:
                                    text: "WATER LEVEL"
                                    theme_text_color: "Custom"
                                    text_color: 0.8, 0.8, 0.8, 1
                                    font_name: "assets/sf_txt_reg.ttf"
                                    font_size: 18
                                    size_hint_y: None
                                    height: self.texture_size[1]

                            MDBoxLayout:
                                orientation: 'vertical'
                                size_hint: 1, 0.18
                                valign: 'bottom'

                                MDLabel:
                                    text: "2.0 L"
                                    theme_text_color: "Custom"
                                    text_color: 0.2, 0.8, 0.2, 1  # Green
                                    font_name: "assets/sf_mono_bold.otf"
                                    font_size: 30
                                    size_hint_y: None
                                    height: self.texture_size[1]

                                MDLabel:
                                    text: "WATER VOLUME"
                                    theme_text_color: "Custom"
                                    text_color: 0.8, 0.8, 0.8, 1
                                    font_name: "assets/sf_txt_reg.ttf"
                                    font_size: 18
                                    size_hint_y: None
                                    height: self.texture_size[1]

                            MDSeparator:

                            MDBoxLayout:
                                orientation: 'vertical'
                                size_hint: 1, 0.42
                                spacing: 12

                                PillToggleButton:
                                    id: toggle_aerator
                                    size_hint: 1, None
                                    height: 56
                                    markup: True
                                    text: "[font=assets/sf_txt_bold.ttf][size=24]OPERATING[/font][/size]\\n[size=20][font=assets/sf_txt_reg.ttf]AERATOR[/font][/size]" if self.is_active else "[font=assets/sf_txt_bold.ttf][size=24]IDLE[/font][/size]\\n[size=20][font=assets/sf_txt_reg.ttf]AERATOR[/font][/size]"
                                    halign: 'center'
                                    color_on: '#0078ff'
                                    color_off: 0, 0.47, 1, 0.2
                                    line_height: 0.9
                                    cmd_on: app.talk_to_ard("aerator_on")
                                    cmd_on: app.talk_to_ard("aerator_off")

                                PillToggleButton:
                                    id: toggle_led_panels
                                    size_hint: 1, None
                                    height: 56
                                    markup: True
                                    text: "[font=assets/sf_txt_bold.ttf][size=24]ON[/font][/size]\\n[size=20][font=assets/sf_txt_reg.ttf]LED PANELS[/font][/size]" if self.is_active else "[font=assets/sf_txt_bold.ttf][size=24]OFF[/font][/size]\\n[size=20][font=assets/sf_txt_reg.ttf]LED PANELS[/font][/size]"
                                    halign: 'center'
                                    color_on: 'ccba00'
                                    color_off: 0.8, 0.73, 0, 0.2
                                    line_height: 0.9
                                    cmd_on: app.talk_to_ard("led_on")
                                    cmd_on: app.talk_to_ard("led_off")

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
                                do_scroll_x: False
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

                                DebounceBtn:
                                    text: "COUNT" if app.is_counting else "+SUB-BATCH"
                                    size_hint: 1, None
                                    height: 56
                                    font_size: 24
                                    font_name: "assets/sf_txt_bold.ttf"
                                    background_normal: "res/btn_pill_blue_l.png"
                                    background_down: "res/btn_pill_blue_l_down.png"
                                    on_release:
                                        app.count_on_click() if self._can_press else None
                                
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
        padding: [12, 12, 12, 0]
        spacing: 12

        MDBoxLayout:
            size_hint: 1, None
            height: 36
            spacing: 12

            Button:
                id: btn_bck_dashboard
                text: "Dashboard"
                font_name: "assets/sf_txt_reg.ttf"
                font_size: 18
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
                source: f"res/ic_wifi_{app.wifi_stat[app.wifi_strength]}.png"
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
                    on_release: 
                        app.show_wifi_dialog() if app.wifi_on else None

                    Image:
                        size_hint: None, None
                        source: "res/ic_wifi_blue.png"
                        width: 36
                        height: 36
                        allow_stretch: True
                        keep_ratio: True
                        pos_hint: {"center_y": .5}

                    MDLabel:
                        text: "Wi-Fi"
                        halign: 'left'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        size_hint_x: 1

                    MDLabel:
                        id: txt_conn_stat_ssid
                        text: "Connected to SSID"
                        halign: 'right'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 0.5
                        size_hint_x: 1

                    WiFiToggleSwitch:
                        id: toggle_wifi 
                        on_release: app.toggle_wifi(self.active)
                        pos_hint: {"center_y": .5}

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
                                rgba: 0.25, 0.25, 0.25, 1
                            Line:
                                width: 4 
                                cap: 'round'
                                points: [self.x + self.padding, self.center_y, self.right - self.padding, self.center_y]

                MDCard:
                    orientation: 'vertical'
                    size_hint: 1, None
                    height: self.minimum_height
                    padding: [19, 0, 19, 0]

                    ClickableMDLabel:
                        text: "Sync Logs to Cloud"
                        halign: 'left'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: '#008ade'
                        size_hint: 1, None
                        height: 64
                        on_release: app.sync_db_logs_thread(show_snackbar = True)

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

                    ClickableMDLabel:
                        text: "Clear Locally Stored Logs"
                        halign: 'left'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: '#db3838'
                        size_hint: 1, None
                        height: 64
                        on_release: app.wipe_local_logs(show_dialog=True)

                MDCard:
                    orientation: 'horizontal'
                    size_hint: 1, None
                    height: 64
                    padding: 12
                    spacing: 12
                    on_release: app.exit_program()

                    MDLabel:
                        text: "Exit Program"
                        halign: 'center'
                        pos_hint: {"center_y": .5}
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: '#db3838'
                        size_hint: 1, None
                        height: 64

# --------------------------------------------------LOGS PAGE-------------------------------------------------------
<LogsScreen>:
    name: "logs"
    md_bg_color: 0.08, 0.08, 0.08, 1
    on_enter: app.sync_db_logs_thread(show_snackbar=False)

    MDBoxLayout:
        orientation: 'vertical'
        size_hint_y: 1
        padding: [12, 12, 12, 0]
        spacing: 12

        MDBoxLayout:
            size_hint: 1, None
            height: 36
            spacing: 12

            Button:
                id: logs_btn_bck_dashboard
                text: "Dashboard"
                font_name: "assets/sf_txt_reg.ttf"
                font_size: 18
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
                source: f"res/ic_wifi_{app.wifi_stat[app.wifi_strength]}.png"
                width: 26
                height: 26
                allow_stretch: True
                keep_ratio: 
                pos_hint: {"center_y": .5}

            Button:
                id: logs_btn_bck_dashboard
                text: "Sync Logs"
                font_name: "assets/sf_txt_reg.ttf"
                font_size: 18
                background_normal: "res/btn_pill_gray_s.png"
                background_down: "res/btn_pill_gray_s_down.png"
                size_hint_x: None
                width: self.texture_size[0] + 24
                height: self.texture_size[1]
                on_release: app.sync_db_logs_thread(show_snackbar = True)

        RecycleView:
            id: logs_recycle_view
            viewclass: 'BatchLogItem'
            
            # This layout manager handles the scrolling math
            RecycleBoxLayout:
                default_size: None, 250 # Approximate starting height of your card
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'
                spacing: dp(15)
                padding: dp(20)
# --------------------------------------------------CUSTOM CLASSES-------------------------------------------------------
<Snackbar>:
    id: snackbar
    orientation: "horizontal"
    size_hint: None, None
    size: 480, 48
    opacity: 0
    pos_hint: {"center_x": 0.5, "center_y": 0.05} 
    spacing: 10
    padding: 14
    elevation: 3
    shadow_color: 0, 0, 0, 0.2

    canvas.before:
        Color:
            rgba: 1, 1, 1, 1 
            
        BorderImage:
            pos: self.pos
            size: self.size
            source: 'res/bg_snackbar_red.png' if root.warning_mode else 'res/bg_snackbar_white.png'
            border: [24, 24, 24, 24]

    Image:
        id: toast_icon
        size_hint: None, None
        source: 'res/ic_warn_s.png' if root.warning_mode else 'res/ic_info_s.png'
        width: 26
        height: 26
        allow_stretch: True
        keep_ratio: True
        pos_hint: {"center_y": .5}

    
    MDLabel:
        id: toast_text
        text: self.text
        font_name: 'assets/sf_txt_reg.ttf'
        font_size: 20
        theme_text_color: "Custom"
        text_color: (1, 1, 1, 1) if root.warning_mode else (0, 0, 0, 1)
        halign: 'left'
        width: self.texture_size[0]

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

<WifiConnectDialog@Popup>
    width: 500
    height: 364
    size_hint: None, None
    background: ''
    background_color: 0, 0, 0, 0
    separator_height: 0
    title: ""
    auto_dismiss: False

    MDBoxLayout:
        orientation: 'vertical'
        size_hint: 1, None
        height: 364
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
            size_hint: 1, 1
            spacing: 12
            padding: [15, 10, 15, 8]

            MDLabel:
                text: "Connect to a Wi-Fi Network" if not app.is_online else "Change Wi-Fi Network"
                font_name: "assets/sf_txt_bold.ttf"
                font_size: 24
                text_color: 1, 1, 1, 1
                size_hint_x: 1
                halign: 'left'

            MDLabel:
                text: "To change or connect to a Wi-Fi, enter SSID and password. Leave password empty if not required."
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
                id: input_ssid
                hint_text: "Enter Network Name/SSID"
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
                id: input_password
                hint_text: "Enter password"
                multiline: False
                password: True
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
                text: "CONNECT"
                size_hint: 1, None
                height: 56
                font_size: 24
                font_name: "assets/sf_txt_bold.ttf"
                background_normal: "res/btn_pill_blue_l.png"
                background_down: "res/btn_pill_blue_l_down.png"
                on_release:
                    app.connect_to_new_wifi(input_ssid.text, input_password.text)

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

<WiFiToggleSwitch>:
    # Set a default fixed size for the switch
    size_hint: None, None
    size: dp(60), dp(30)
    
    canvas:
        Color:
            rgba: (0.2, 0.8, 0.4, 1) if self.active else (0.3, 0.3, 0.3, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.height / 2]

        Color:
            rgba: (1, 1, 1, 1)
        RoundedRectangle:
            pos: self.x + self.knob_pos, self.y + dp(2)
            size: self.height - dp(4), self.height - dp(4)
            radius: [(self.height - dp(4)) / 2]

<BatchLogItem>
    orientation: 'vertical'
    padding: 19
    size_hint: 1, None
    height: 275
    radius: [16, 16, 16, 16]
    spacing: 8
    line_color: '#353535'
    line_width: 1.0

    MDBoxLayout:
        orientation: 'horizontal'
        size_hint_x: 1
        size_hint_y: None
        height: 36

        MDLabel:
            size_hint_x: 1
            size_hint_y: None
            height: self.texture_size[1]
            font_size: 24
            font_name: 'assets/sf_mono_reg.otf'
            theme_text_color: "Custom"
            text_color: 0.5, 0.5, 0.5, 1
            text: root.log_timestamp
            halign: 'left'

        Button:
            id: btn_bck_dashboard
            text: "DELETE"
            font_name: "assets/sf_txt_reg.ttf"
            font_size: 18
            background_normal: "res/btn_pill_gray_s.png"
            background_down: "res/btn_pill_gray_s_down.png"
            size_hint_x: None
            width: self.texture_size[0] + 24
            height: self.texture_size[1]
            on_release: app.del_log_entry(target_uuid=root.log_uuid, show_dialog=True)

    MDLabel:
        markup: True
        size_hint_x: 1
        size_hint_y: None
        height: self.texture_size[1]
        font_size: 24
        halign: 'left'
        text: f"[font=assets/sf_mono_bold.otf][color=#ffffff]BATCH ID: [/font][/color][font=assets/sf_mono_reg.otf][color=#ffff00]{root.log_id_batch}[/font][/color]"
    
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
        text: f"[font=assets/sf_mono_reg.otf][color=#ffffff]MARGIN OF ERROR: [/font][/color][font=assets/sf_mono_reg.otf][color=#db3838]{root.log_margin_of_err:.2f}[/font][/color]"

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

def config_conn_wifi(ssid, password):
    try:
        subprocess.check_call([
            'nmcli', 'connection', 'add', 
            'type', 'wifi', 
            'con-name', ssid, 
            'ifname', 'wlan0', 
            'ssid', ssid, 
            'wifi-sec.key-mgmt', 'wpa-psk', 
            'wifi-sec.psk', password
        ])

        subprocess.check_call([
            'nmcli', 'connection', 'up', ssid
        ])
        return True
    except subprocess.CalledProcessError:
        # Wrong password or network out of range
        return False

def get_initial_wifi_stat():
    try:
        result = subprocess.run(
            ["nmcli", "radio", "wifi"], 
            capture_output=True, 
            text=True, 
            timeout=2
            )
        return result.stdout.strip().lower() == "enabled"

    except Exception as e:
        print(f"[DEBUG] Failed to read initial state: {e}")
        return False

def set_wifi_state(enable: bool):
        cmd = "on" if enable else "off"
        try:
            subprocess.run(
                ["nmcli", "radio", "wifi", cmd],
                capture_output=True,
                check=True,
                timeout=5
            )
            print(f"[INFO] Wi-Fi is set to: {cmd}")
        except Exception as e:
            print(f"[DEBUG] Error toggling Wi-Fi state: {e}")

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
    pass

class UlangSystemApp(MDApp):
#===STATUS
    count_active = BooleanProperty(False) # For switching UI interface mode
    is_counting = BooleanProperty(False) # Inferernce active state
    is_cam_initializing = BooleanProperty(False)

    # Connectivity Status
    is_online = BooleanProperty(False)
    wifi_on = BooleanProperty(False)
    wifi_stat = ['disconnected', '1', '2', '3', '4']
    wifi_strength = NumericProperty(0)

#===PLACEHOLDERS
    dialog = None
    snackbar = None

    sub_batch_history = {}
    payload = {
        "log_uuid": None, #Auto-generated
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
    empty_chamber = True

#===CLIENT CREATION
    SUPABASE_API_URL = 'https://nltmvrjxasslpqbdyamg.supabase.co'
    SUPABASE_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5sdG12cmp4YXNzbHBxYmR5YW1nIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM2MjcwNzUsImV4cCI6MjA5OTIwMzA3NX0.LCwGdbW5DVKSjl8Qql65LjQQgjOYMkhre7y3q94Eo68'

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"

        wifi_init_stat = get_initial_wifi_stat()

        # If wifi is off do not check for connectivity
        if wifi_init_stat:
            self.wifi_on = wifi_init_stat
            self.is_online = wifi_init_stat
            print("[INFO] Wifi status on build: ON")
        else: 
            self.wifi_on = False
            print("[INFO] Wifi status on build: OFF")

        Clock.schedule_interval(self.update_wifi_stat, 2.0)

        try:
            self.db_client: Client = create_client(self.SUPABASE_API_URL, self.SUPABASE_API_KEY)
            print("[INFO] Successfully connected to Supabase Cloud.")

        except Exception as e:
            err = e
            print(f"[WARNING] Cloud connection failed. Running offline. Error: {err}")

        Window.bind(on_key_down=self.on_keyboard_down)
        return Builder.load_string(INTERFACE)

    def on_start(self):
        """Called automatically after the app builds. We set up GPIO here."""
        self.right_pane = self.root.ids.dashboard_screen.ids.data_pane_sm
        self.right_pane.current = "panel_count_inactive"
        self.btm_btn = self.root.ids.dashboard_screen.ids.btm_btn_container
        self.btm_btn.current = "btn_count_inactive"
        self.aerator = self.root.ids.dashboard_screen.ids.toggle_aerator
        self.led_panels = self.root.ids.dashboard_screen.ids.toggle_led_panels
        self.sub_batch_scrollview = self.root.ids.dashboard_screen.ids.sub_batch_scrollview

        if not self.is_online:
            self.show_snackbar(message = "System is Running Offline", warning_mode=False)

        if GPIO_AVAILABLE:
            self.btn_settings = HardwareButton(17)
            self.btn_settings.when_pressed = lambda: Clock.schedule_once(self.go_to_settings)

            self.btn_home = HardwareButton(27)
            self.btn_home.when_pressed = lambda: Clock.schedule_once(self.hboard)

            self.btn_start = HardwareButton(22)
            self.btn_start.when_pressed = lambda: Clock.schedule_once(self.start_batch_count)

        #Initialize camera
        self.start_camera_loading()
        listener = threading.Thread(target=self.listen_to_ard, daemon=True)
        listener.start()

    @mainthread
    def update_sensor_reads(self, data):
        """@mainthread: Updates the screen with the JSON data"""
        # Because we used on_start, we know for a fact these IDs exist!
        self.root.ids.dashboard_screen.ids.water_temp_label.text = f"{data.get('temp')} °C"
        self.root.ids.dashboard_screen.ids.water_lvl_label.text = f"{data.get('light')} Lux"

    def listen_to_ard(self):
        """
        Background thread (The Chef): Continuously listens for incoming sensor 
        data so the Kivy UI never freezes.
        """
        while True:
            if arduino.in_waiting > 0:
                try:
                    # Read the line until \n and decode it
                    raw_data = arduino.readline().decode('utf-8').strip()
                    
                    # Parse the JSON
                    sensor_data = json.loads(raw_data)
                    
                    print(f"[Sensors Updated] Temp: {sensor_data.get('temp')}°C, Light: {sensor_data.get('light')}")
                    
                    self.update_sensor_reads(sensor_data)
                    
                except json.JSONDecodeError:
                    print("Failed to decode JSON from Arduino.")

            time.sleep(0.05)

    def talk_to_ard(self, action):
        """
        Triggered by the Main UI Thread when a technician taps a Kivy button.
        """
        command_dict = {"command": action}
        
        # Convert Python dictionary to JSON string and add the newline delimiter
        json_string = json.dumps(command_dict) + "\n"
        
        # Send it down the USB wire
        arduino.write(json_string.encode('utf-8'))
        print(f"Sent command to Arduino: {action}")

    def exit_program(self):
        print("[INFO] System shutting down...")
        self.stop_camera()
        self.stop()

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

    def get_fade_transition(self):
        return FadeTransition(duration=0.1)

#===Camera Live Feed Functions
    def start_camera_loading(self):
        """1. Resets the UI and spawns the background worker."""
        if hasattr(self, 'picam2') or self.is_cam_initializing:
            return
        self.is_cam_initializing = True
        self.root.ids.dashboard_screen.ids.camfeed_pane.current = "camfeed_loading_screen"

        threading.Thread(target=self._init_hardware, daemon=True).start()

    def _init_hardware(self):
        """@backgroundthread: Initializes capturing and loading AI model"""
        try:
            self.picam2 = Picamera2()

            vd_config =self.picam2.create_video_configuration(
                main={"size": (1920,1080), "format": "RGB888"}
            )
            self.picam2.configure(vd_config)
            self.picam2.start_preview(Preview.NULL)
            self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
            self.picam2.start()
            self.model = YOLO("models/pre-trained/ulangn-obb_v3-1_ncnn_model")
            self._camera_ready()
            self._run_inf_loop()

        except Exception as e:
            print(f"[ERROR] Camera init failed: {e}")
        finally:
            self.is_cam_initializing = False

    @mainthread
    def _camera_ready(self):
        """@mainthread: Swaps camfeed_pane with camera live feed"""
        self.root.ids.dashboard_screen.ids.camfeed_pane.current = "camfeed_live_screen"

    def _run_inf_loop(self):
        """@backgroundthread: Grabs camera live feed frames, runs inference, pass to UI"""
        targ_fps = 10
        targ_frame_time = 1/targ_fps

        while True:
            sttime = time.time()

            #ret, frame = self.capture.read()
            #if not ret:
            #    continue

            hi_res_frame = self.picam2.capture_array()

            try:
                inf_result = self.model.predict(hi_res_frame, conf=0.50, verbose=False)

                if inf_result[0].obb is not None:
                    inf_count = len(inf_result[0].obb)
                else:
                    inf_count = 0

                inf_wframe = inf_result[0].plot(labels=False, line_width=2, conf=False)

                disp_frame = cv2.resize(inf_wframe, (434, 244), interpolation=cv2.INTER_LINEAR)
                rgb_frame = cv2.cvtColor(disp_frame, cv2.COLOR_BGR2RGB)

                frame_bytes = rgb_frame.tobytes()
 
                self.update_feed(frame_bytes, 434, 244, inf_count)

                eltime = time.time()-sttime
                print(f"[INFO] Inference Loop Speed: {(eltime*1000):.2f}ms")
                slptime = targ_frame_time-eltime
                if slptime>0:
                    time.sleep(slptime)

            except Exception as e:
                print(f"[DEBUG] {e}")
                traceback.print_exc()

    @mainthread
    def update_feed(self, frame_bytes, width, height, total_count):
        """@mainthread: Refresh camera_feed"""
        texture = Texture.create(size=(width, height), colorfmt='rgb')
        texture.blit_buffer(frame_bytes, colorfmt='rgb', bufferfmt='ubyte')

        texture.flip_vertical()

        cam_widget = self.root.ids.dashboard_screen.ids.camera_feed
        cam_widget.texture = texture
        cam_widget.canvas.ask_update()
        
        print(f"[INFO|COUNTING] Count: {total_count}")

    def stop_camera(self):
        """Cleans up memory when navigating away"""
        if hasattr(self, 'picam2'):
            try:
                self.picam2.stop()
                self.picam2.close()
            except Exception as e:
                print(f"[DEBUG] Camera stop error: {e}")
            finally:
                delattr(self, 'picam2')
        self.is_cam_initializing = False

#===Wifi Configuration Commands
    def update_wifi_stat(self, dt=0):
        wifi_text_widget = self.root.ids.settings_screen.ids.txt_conn_stat_ssid

        def execute_update():
            status = self.get_wifi_stat()
            self.is_online = status["connected"]
            
            if not status["connected"]:
                self.wifi_strength = 0
                wifi_text_widget.text = "Disconnected"
                return
                
            # Update the network name on settings
            wifi_text_widget.text = f"Connected to {status['ssid']}"
            # Map signal strength (0-100)
            strength = status["strength"]
            if strength >= 75:
                self.wifi_strength = 4
            elif strength >= 50:
                self.wifi_strength = 3
            elif strength >= 25:
                self.wifi_strength = 2
            elif strength > 0:
                self.wifi_strength = 1

        if self.wifi_on:
            execute_update()
        else:
            self.wifi_strength = 0
            wifi_text_widget.text = "Off"

    def get_wifi_stat(self):
        try:
            result = subprocess.check_output(
                ['nmcli', '-t', '-f', 'active,ssid,signal', 'dev', 'wifi'],
                text=True
            )
            # Parse the output line by line
            for line in result.split('\n'):
                # Line format yes:My_Network_Name:85
                if line.startswith('yes'):
                    parts = line.split(':')
                    return {
                        "connected": True, 
                        "ssid": parts[1], 
                        "strength": int(parts[2]) # 0 to 100
                    }

            return {"connected": False, "ssid": "Disconnected", "strength": 0}
            
        except subprocess.CalledProcessError:
            return {"connected": False, "ssid": "Error", "strength": 0}
        except Exception as e:
            return {"connected": False, "ssid": "Error", "strength": 0}
        
    def connect_to_new_wifi(self, ssid, password):
        connected = config_conn_wifi(ssid, password) 
        if connected:
            self.show_snackbar(message = f"Connected to {ssid}")
            self.popup.dismiss()
        else:
            self.show_snackbar(message="Failed to connect to the Network", warning_mode=True)

    def toggle_wifi(self, value):
        self.wifi_on = not value
        self.update_wifi_stat()

#==================================================SCREEN NAVIGATION FUNCTIONS===============================================
 
    def go_to_settings(self, *args):
        if self.root.current != "settings":
            self.root.transition.direction = "left"
            self.root.current = "settings"

        self.stop_camera()

    def go_to_logs(self, *args):
        if self.root.current != "logs":
            self.root.transition.direction = "left"
            self.root.current = "logs"

        self.stop_camera()

    def go_to_dashboard(self, *args):
        if self.root.current != "dashboard":
            self.root.transition.direction = "right"
            self.root.current = "dashboard"

        self.start_camera_loading()

#============================================================================================================================

    def start_batch_count(self, *args):
        if self.root.current == "dashboard":
            dashboard_screen = self.root.get_screen("dashboard")
            # Later, this is where you will tell OpenCV and YOLOv8 to start processing frames!

    def show_entry_details(self, *args):
        self.popup = Factory.BatchCountDialog()
        self.popup.open()

    def show_wifi_dialog(self, *args):
        self.popup = Factory.WifiConnectDialog()
        self.popup.open()

    def activate_count(self, input_name_batch = "", input_name_op = "", *args):
        self.name_count_batch = input_name_batch
        self.name_operator = input_name_op
    
        def execute_activation():
            self.count_active = True
            print('[INFO] Counting Process Activated')
            self.popup.dismiss()
            self.aerator.is_active = False
            self.aerator.is_toggleable = False
            self.led_panels.is_active = True
            self.led_panels.is_toggleable = False
            self.right_pane.current = "panel_count_active"
            self.btm_btn.current = "btn_count_active"
            print(f"[INFO] Count started for: {self.name_count_batch}.\nOperated by: {self.name_operator}")

        if not (self.name_count_batch and self.name_operator):
            self.show_snackbar(warning_mode=True, message="Batch detail entries are required.")
        else:
            execute_activation()

    def deactivate_count(self, abort = False, *args):
        def execute_deactivation():
            self.count_active = False
            print('[INFO] Counting Process Deactivated')
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
            self.total_batches_created = 0
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
        if getattr(self, 'snackbar', None) is None:
            self.snackbar = Snackbar()

        self.snackbar.warning_mode = warning_mode
        self.snackbar.ids.toast_text.text = message

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
            print(f"[INFO] Removed {widget_to_remove.batch_name}. Current Backend Data:", self.sub_batch_history)
#-------Show a confirmation dialog
        dialog = SystemDialog(
            dialog_title = "Remove Sub-batch",
            dialog_msg = "Are you sure you want to remove this Sub-batch? This process cannot be undone.", 
            mode = "destructive", 
            command_on_proceed = execute_deletion)
        dialog.open()

#=======================================================Database Functions=============================================================
    def save_batch_log(self):
        new_loguuid = str(uuid.uuid4())
        self.payload.update({
            "log_uuid": new_loguuid,
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
                print("[INFO] Log Saved to Database:")

                for key, value in cached_payload.items():
                    print(f"{key}: {value} | type: {type(value)}")

                Clock.schedule_once(lambda dt: self.show_snackbar(warning_mode = False, message=f"{cached_payload['batch_id']} is saved to Logs"))

            except Exception as e:
                err = e
                print(f"[DEBUG] Failed to Push Batch Count Log on Database: {err}")
                save_to_local()
                Clock.schedule_once(lambda dt: self.show_snackbar(warning_mode=True, message=f"Failed to push log on cloud, log is saved locally"))

        def save_to_local():
            try:
                folder_name = "pending_sync"
                os.makedirs(folder_name, exist_ok=True) 

                filename = f"{cached_payload['log_uuid']}.json"
                filepath = os.path.join(folder_name, filename)

                with open(filepath, "w") as json_file:
                    json.dump(cached_payload, json_file, indent=4) 
                print(f"[INFO] Local Backup created at {filepath}")
                Clock.schedule_once(lambda dt: self.show_snackbar(warning_mode=True, message="System offline, log saved locally."))
                
            except Exception as e:
                print(f"[DEBUG] CRITICAL HARDWARE ERROR: Failed to save local file! {e}")

        if self.is_online:
            threading.Thread(target=push_data).start()
        else:    
            save_to_local()

    def wipe_local_logs(self, show_dialog: bool = False, *args):
        db_directory = "pending_sync/"

        def execute_wipe_local_logs():
            if os.path.exists(db_directory):
                log_files = glob.glob(os.path.join(db_directory, "*.json"))

                if log_files:
                    for file_path in log_files:
                        try:
                            os.remove(file_path)
                            self.show_snackbar(warning_mode=False, message="Local logs permanently deleted")
                            print(f"[INFO] {file_path} permanently deleted")
                        except Exception as e:
                            print(f"[DEBUG] System Warning: Could not delete {file_path} - {e}")
                            self.show_snackbar(message="Failed to wipe local logs")

                else:
                    self.show_snackbar(warning_mode=False, message="Local logs already empty")

        if show_dialog:
            dialog = SystemDialog(dialog_title = "Wipe Local Logs", 
                                  dialog_msg = "This will permanently delete all offline logs. Cloud backups will remain safe.", 
                                  mode="destructive", 
                                  command_on_proceed=execute_wipe_local_logs)
            dialog.open()

        else: 
            execute_wipe_local_logs()

    def sync_db_logs(self, show_snackbar = False):
        master_log_list = []
        sync_succeed = False
        pending_folder = "pending_sync"

        # LOAD CLOUD (OR LOCAL HISTORY) LOGS
        try:
            response = self.db_client.table("batch_count_history_logs").select("*").order("timestamp", desc=True).limit(50).execute()
            
            for cloud_log in response.data:
                cloud_log["log_loc"] = "cloud"
                master_log_list.append(cloud_log)
            sync_succeed = True

        except Exception as e:
            sync_succeed = False
            print(f"[DEBUG] Offline Mode Active. Could not reach Supabase: {e}")

        if os.path.exists(pending_folder):
            for filename in os.listdir(pending_folder):
                if filename.endswith(".json"):
                    filepath = os.path.join(pending_folder, filename)
                    try:
                        with open(filepath, "r") as f:
                            log_data = json.load(f)

                        if sync_succeed:
                            try:
                                # Push to Supabase
                                self.db_client.table("batch_count_history_logs").insert(log_data).execute()
                                print(f"[DEBUG] Successfully synced {filename} to Cloud!")
                                
                                # Delete the local file once uploaded
                                os.remove(filepath)
                                
                                # Add to UI list as synced
                                log_data["log_loc"] = "cloud"
                                master_log_list.append(log_data)
                                
                                continue
                                
                            except Exception as upload_error:
                                print(f"[DEBUG] Failed to upload {filename}: {upload_error}")

                        log_data["log_loc"] = "local" 
                        master_log_list.append(log_data)
                    except Exception as e:
                        print(f"[DEBUG] Error reading local log {filename}: {e}")

        # SORT THE MERGED LIST BY TIMESTAMP
        try:
            master_log_list.sort(
                key=lambda x: datetime.strptime(x["timestamp"], "%b %d, %Y %I:%M %p"), 
                reverse=True
            )
        except Exception as e:
            print(f"[DEBUG] Sorting error (likely a timestamp format mismatch): {e}")

        #FORMAT FOR RECYCLEVIEW & UPDATE UI
        rv_data = []
        for log in master_log_list:
            rv_data.append({
                "log_uuid": str(log.get("log_uuid", "NULL")),
                "log_id_batch": str(log.get("batch_id", "UNKNOWN")),
                "log_timestamp": str(log.get("timestamp", "No Date")),
                "log_name_op": str(log.get("op_name", "Unknown Operator")),
                "log_pl_count": int(log.get("total_pl_count", 0)),
                "log_num_sbatches": int(log.get("num_of_sbatch", 0)),
                "log_margin_of_err": float(log.get("accuracy", 0.0)),
                "log_loc": str(log.get("log_loc", "UNKNOWN"))
            })

        Clock.schedule_once(lambda dt: self.update_rv(rv_data))

        if show_snackbar:
            Clock.schedule_once(lambda dt: self.show_snackbar(warning_mode = not sync_succeed, message="Synced Successfully" if sync_succeed else "Sync Failed!"))

    def sync_db_logs_thread(self, show_snackbar: bool=False, *args):
        threading.Thread(target=self.sync_db_logs, args=(show_snackbar,)).start()

    def update_rv(self, formatted_data):
            self.root.ids.logs_screen.ids.logs_recycle_view.data = formatted_data

    def del_log_entry(self, target_uuid:str="", show_dialog:bool=True, **args):
        def del_from_db():
            try:
                self.db_client.table("batch_count_history_logs").delete().eq("log_uuid", target_uuid).execute()
                rv.data = [item for item in rv.data if item.get('log_uuid') != target_uuid]
                print(f"[INFO] {target_uuid} is successfully removed from database")
                self.show_snackbar(message="Successfully removed from Database", warning_mode=False)
            except Exception as e:
                print(f"[DEBUG] Cloud delete failed (offline?): {e}")
                self.show_snackbar(message="Failed to remove from Database", warning_mode=True)

        def del_from_local():
            try:
                # Set uuid as filename
                file_path = f"pending_sync/{target_uuid}.json" 
                if os.path.exists(file_path):
                    os.remove(file_path)
                    rv.data = [item for item in rv.data if item.get('log_uuid') != target_uuid]
                    print(f"[INFO] {file_path} is successfully removed from local logs")
                    self.show_snackbar(message="Successfully removed from Local Logs", warning_mode=False)
            except Exception as e:
                print(f"[DEBUG] Local delete failed: {e}")
                self.show_snackbar(message="Failed to remove from Local Logs", warning_mode=True)

        rv = self.root.ids.logs_screen.ids.logs_recycle_view
        target_item = next((item for item in rv.data if item.get('log_uuid') == target_uuid), None)

        if not target_item:
            print("[ERROR] Could not find the target log in the RecycleView.")
            return

        del_cmd = del_from_db if target_item.get("log_loc") == "cloud" else del_from_local

        if show_dialog:
            SystemDialog(
                dialog_title = "Delete Log Item",
                dialog_msg = "Are you sure you want to delete this log? This process cannot be undone.",
                mode = 'destructive',
                command_on_proceed = del_cmd
                ).open()
        else:
            del_cmd()

class PillToggleButton(Button):
    is_toggleable = BooleanProperty(True)
    is_active = BooleanProperty(False)

    color_on = ColorProperty([0.1, 0.6, 0.2, 1])
    color_off = ColorProperty([0.25, 0.25, 0.25, 1])
    color_pressed = ColorProperty([0.4, 0.4, 0.4, 1])

    current_color = ColorProperty([0.25, 0.25, 0.25, 1])
    cmd_on = ObjectProperty(None, allownone = True)
    cmd_off = ObjectProperty(None, allownone = True)

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
            if self.cmd_on and callable(self.cmd_on): 
                self.cmd_on()
        else:
            self.current_color = self.color_off
            if self.cmd_on and callable(self.cmd_on): 
                self.cmd_off()

class WiFiToggleSwitch(ButtonBehavior, Widget):
    active = BooleanProperty(False)
    knob_pos = NumericProperty(dp(2))    
    _initializing = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        threading.Thread(target=get_initial_wifi_stat, daemon=True).start()

    def _get_initial_wifi_stat(self):
        is_on = get_initial_wifi_stat()
        if is_on:
            Clock.schedule_once(lambda dt: self._set_initial_state(is_on))
        else:
            self._initializing = False

    def on_release(self):
        self.active = not self.active

    def on_active(self, instance, value):
        if value:
            target_x = self.width - self.height + dp(2)
        else:
            target_x = dp(2)
        anim = Animation(knob_pos=target_x, duration=0.2, t='out_quad')
        anim.start(self)

        if self._initializing:
            return
        
        threading.Thread(target=set_wifi_state, args=(value,), daemon=True).start()

    def _set_initial_state(self, is_on):
        self.active = is_on
        self.knob_pos = self.width - self.height + dp(2) if is_on else dp(2)
        #DEBUG
        print(f"[DEBUG] Wifi state on initialization: {'ON' if is_on else 'OFF'}")
        self._initializing = False

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
        if self.command_on_proceed and callable(self.command_on_proceed): 
            self.command_on_proceed()
        self.dismiss()

class Snackbar(MDBoxLayout):
    warning_mode = BooleanProperty(False)

class BatchLogItem(MDCard):
    log_uuid = StringProperty("")
    log_timestamp = StringProperty("")
    log_id_batch = StringProperty("")
    log_name_op = StringProperty("")
    log_pl_count = NumericProperty(0)
    log_num_sbatches = NumericProperty(0)
    log_margin_of_err = NumericProperty(0.0)

# Custom Button for Count/+Sub-batch to avoid double-clicking issue on touchscreen
class DebounceBtn(Button):
    debounce_time = 0.5

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._can_press = True

    def on_release(self):
        if not self._can_press:
            print("[INFO] DebounceBtn: A press is swallowed.")
            return True

        self._can_press = False
        Clock.schedule_once(self._enable_press, self.debounce_time)

        return super().on_release()

    def _enable_press(self, dt):
        self._can_press = True

class ClickableMDLabel(ButtonBehavior, MDLabel):
    pass

if __name__ == '__main__':
    UlangSystemApp().run()