import faulthandler
faulthandler.enable()

from supabase import create_client, Client
import threading
import copy
import json
import os
import uuid
import subprocess
import glob
import time
from datetime import datetime, timedelta

import serial

import traceback

import cv2

import smtplib
import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from ultralytics import YOLO
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

from shapely.geometry import Polygon
from shapely.ops import unary_union

#Kivy Configurations
from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemandmulti')
Config.set('graphics', 'fullscreen', 'auto')
Config.set('graphics', 'resizable', False)

from kivy.utils import get_color_from_hex
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
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.animation import Animation
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior

# HARDWARE GPIO SETUP
from picamera2 import Picamera2, Preview
from libcamera import controls

try:
    from gpiozero import Button as HardwareButton
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[Warning] gpiozero not found. Physical GPIO buttons disabled (Running on Laptop).")
    
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
    FullScreen: 
        id: full_view

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
                line_color: '#505050'
                line_width: 0.5

                RelativeLayout:
                    size_hint: 1, 1

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
                                
                                Image:
                                    size_hint: None, None
                                    size: 72, 72
                                    allow_stretch: True
                                    pos_hint: {'center_x': .5}
                                    active: True
                                    source: 'res/ic_camera.png'
                                    
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

                        MDScreen:
                            name: "camfeed_alert_screen"

                            MDBoxLayout:
                                orientation: 'vertical'
                                adaptive_height: True
                                pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                                spacing: 24
                                padding: 16

                                Image:
                                    id: ic_alert
                                    size_hint: None, None
                                    height: 72
                                    width: 72
                                    allow_stretch:
                                    keep_ratio: True
                                    pos_hint: {"center_x":0.5}

                                MDLabel:
                                    id: txt_alert_title
                                    text: "Warning!"
                                    font_name: "assets/sf_txt_bold.ttf"
                                    font_size: 24
                                    halign: "center"
                                    theme_text_color: "Custom"
                                    text_color: app.color_palette["red"]
                                    valign: "center"

                                MDLabel:
                                    id: txt_alert_message
                                    text: "Warning message."
                                    font_name: "assets/sf_txt_reg.ttf"
                                    font_size: 18
                                    halign: "center"
                                    theme_text_color: "Custom"
                                    text_color: 1, 1, 1, 1
                                    adaptive_height: True

                                Button:
                                    text: "CONTINUE"
                                    font_name: "assets/sf_txt_bold.ttf"
                                    font_size: 18
                                    background_normal: "res/btn_pill_gray_s.png"
                                    background_down: "res/btn_pill_gray_s_down.png"
                                    size_hint: None, None
                                    height: 36
                                    width: self.texture_size[0] + 24
                                    pos_hint: {"center_x": 0.5}
                                    on_release: app.freeze_alert()

                    MDBoxLayout:
                        id: camfeed_batch_id_view
                        orientation: "vertical"
                        adaptive_size: True
                        padding: [8]
                        pos_hint: {"x": 0.02, "top": 0.97}
                        opacity: 1 if app.count_active else 0

                        canvas.before:
                            Color:
                                rgba: 1, 1, 1, 1 
                            BorderImage:
                                source: 'res/btn_pill_gray_s.png'
                                pos: self.pos
                                size: self.size
                                border: [18, 18, 18, 18]

                        Label:
                            id: id_batch_camfeed
                            text: "BATCH"
                            font_name: "assets/sf_txt_reg.ttf"
                            font_size: 20
                            color: 1, 1, 1, 1
                            opacity: 1 if app.count_active else 0
                            size_hint: None, None
                            size: self.texture_size  # Strictly binds size to text footprint
                            on_texture_size: camfeed_batch_id_view.do_layout()

                    MDBoxLayout:
                        orientation: "vertical"
                        size_hint: None, None
                        width: 140
                        height: 70
                        spacing: 5
                        padding: 10
                        pos_hint: {"x":0.02, "y":0.03}

                        canvas.before:
                            Color:
                                rgba: 1, 1, 1, 1 # Ensure the image renders at full brightness
                            BorderImage:
                                source: 'res/btn_pill_gray_s.png'
                                pos: self.pos
                                size: self.size
                                border: [18, 18, 18, 18]

                        MDLabel:
                            text: "PREDICTED:"
                            font_name: "assets/sf_txt_reg.ttf"
                            font_size: 20
                            halign: "left"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1

                        MDLabel:
                            id: camfeed_count
                            text: "--"
                            font_name: "assets/sf_txt_bold.ttf"
                            font_size: 32
                            halign: "left"
                            theme_text_color: "Custom"
                            adaptive_height: True
                            text_color: app.color_palette["dark_blue"]
                        

                    SysIconButton:
                        icon: "res/ic_expand_s.png"
                        background_normal: "res/btn_pill_gray_s.png"
                        background_down: "res/btn_pill_gray_s_down.png"
                        pos_hint: {"right":0.98, "y":0.03}
                        size_hint: None, None
                        on_release: app.go_full_view()
        
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
                                    text_color: app.color_palette["red"] if app.critical_temp else app.color_palette["green"] 
                                    font_name: "assets/sf_mono_bold.otf"
                                    font_size: 28
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
                                    text_color: app.color_palette["red"] if app.critical_load else app.color_palette["blue"]
                                    font_name: "assets/sf_mono_bold.otf"
                                    font_size: 28
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
                                    id: water_vol_label
                                    text: "--"
                                    theme_text_color: "Custom"
                                    text_color: app.color_palette["red"] if app.critical_load else app.color_palette["blue"]
                                    font_name: "assets/sf_mono_bold.otf"
                                    font_size: 28
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
                                    color_on: app.color_palette["blue"]
                                    color_off: 0, 0.47, 1, 0.2
                                    line_height: 0.9
                                    cmd_on: lambda *args: app.talk_to_ard("aerator_on")
                                    cmd_off: lambda *args: app.talk_to_ard("aerator_off")

                                PillToggleButton:
                                    id: toggle_led_panels
                                    size_hint: 1, None
                                    height: 56
                                    markup: True
                                    text: "[font=assets/sf_txt_bold.ttf][size=24]ON[/font][/size]\\n[size=20][font=assets/sf_txt_reg.ttf]LED PANELS[/font][/size]" if self.is_active else "[font=assets/sf_txt_bold.ttf][size=24]OFF[/font][/size]\\n[size=20][font=assets/sf_txt_reg.ttf]LED PANELS[/font][/size]"
                                    halign: 'center'
                                    color_on: app.color_palette["yellow"]
                                    color_off: 0.8, 0.73, 0, 0.2
                                    line_height: 0.9
                                    cmd_on: lambda *args: app.talk_to_ard("led_on")
                                    cmd_off: lambda *args: app.talk_to_ard("led_off")

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
                                    text: "COUNTING..." if app.is_counting else "COUNT"
                                    size_hint: 1, None
                                    height: 56
                                    font_size: 24
                                    font_name: "assets/sf_txt_bold.ttf"
                                    background_normal: "res/btn_pill_green_l_down.png" if app.is_counting else "res/btn_pill_blue_l.png" 
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

            SysIconButton:
                id: btn_bck_dashboard
                text: "Dashboard"
                icon: "res/ic_back.png"
                background_normal: "res/btn_pill_gray_s.png"
                background_down: "res/btn_pill_gray_s_down.png"
                on_release: app.go_to_dashboard()

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
                        halign: 'right'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 0.5
                        size_hint_x: 1
                        shorten: True
                        shorten_from: 'right'

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
                        min: 10
                        max: 255
                        value: 255
                        step: 5
                        size_hint_x: 0.7
                        value_track: True
                        value_track_color: '#ffff00'
                        cursor_size: 64, 34
                        cursor_image: 'res/slider_cursor.png'
                        background_width: 0
                        on_value: app.config_scrn_brightness(self, self.value)

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
                    spacing: 0

                    MDBoxLayout:
                        orientation: 'horizontal'
                        size_hint: 1, None
                        height: 64
                        spacing: 12

                        MDLabel:
                            text: "Set Minimum Water Temperature"
                            halign: 'left'
                            valign: 'center'
                            font_name: "assets/sf_txt_reg.ttf"
                            font_size: 24
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1
                            size_hint: 1, 1

                        ClickableImage:
                            size_hint: None, None
                            source: "res/ic_plus.png"
                            width: 19
                            height: 19
                            allow_stretch: True
                            keep_ratio: True
                            pos_hint: {"center_y": .5}
                            on_release: app.config_temp_setting(increase=True, param='min')

                        TextInput:
                            id: input_min_temp
                            text: str(app.min_temp)
                            multiline: False
                            input_filter: 'float'
                            input_type: 'number'
                            halign: 'center'
                            valign: 'center'
                            on_text_validate: app.config_temp_setting(input=True, param='min')
                            size_hint: None, None
                            width: 100
                            height: 42
                            padding: [0,8,0,0]
                            background_normal: 'res/bg_txt_field_inactive_opaque.png'
                            background_active: 'res/bg_txt_field_active.png'
                            border: [8, 8, 8, 8]  
                            font_name: "assets/sf_txt_reg.ttf"
                            font_size: 24
                            foreground_color: 1, 1, 1, 1
                            pos_hint: {"center_y": .5}

                        MDLabel:
                            text: "\u00B0 C"
                            halign: 'left'
                            font_name: "assets/sf_txt_reg.ttf"
                            font_size: 24
                            theme_text_color: "Custom"
                            text_color: 0.5, 0.5, 0.5, 1
                            size_hint: None, 1
                            valigh: 'center'
                            width: 40

                        ClickableImage:
                            size_hint: None, None
                            source: "res/ic_minus.png"
                            width: 19
                            height: 19
                            allow_stretch: True
                            keep_ratio: True
                            pos_hint: {"center_y": .5}
                            on_release: app.config_temp_setting(decrease=True, param='min')

                    MDSeparator:

                    MDBoxLayout:
                        orientation: 'horizontal'
                        size_hint: 1, None
                        spacing: 12
                        height: 64

                        MDLabel:
                            text: "Set Maximum Water Temperature"
                            halign: 'left'
                            font_name: "assets/sf_txt_reg.ttf"
                            font_size: 24
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1
                            size_hint: 1, 1
                            valigh: 'center'

                        ClickableImage:
                            size_hint: None, None
                            source: "res/ic_plus.png"
                            width: 19
                            height: 19
                            allow_stretch: True
                            keep_ratio: True
                            pos_hint: {"center_y": .5}
                            on_release: app.config_temp_setting(increase=True, param='max')

                        TextInput:
                            id: input_max_temp
                            text: str(app.max_temp)
                            multiline: False
                            input_filter: 'float'
                            input_type: 'number'
                            on_text_validate: app.config_temp_setting(input=True, param='max')
                            halign: 'center'
                            valign: 'center'
                            size_hint: None, None 
                            width: 100
                            height: 42
                            padding: [0,8,0,0]
                            background_normal: 'res/bg_txt_field_inactive_opaque.png'
                            background_active: 'res/bg_txt_field_active.png'
                            border: [8, 8, 8, 8]  
                            font_name: "assets/sf_txt_reg.ttf"
                            font_size: 24
                            foreground_color: 1, 1, 1, 1
                            pos_hint: {"center_y": .5}

                        MDLabel:
                            text: "\u00B0 C"
                            halign: 'left'
                            font_name: "assets/sf_txt_reg.ttf"
                            font_size: 24
                            theme_text_color: "Custom"
                            text_color: 0.5, 0.5, 0.5, 1
                            size_hint: None, 1
                            width: 40
                            valigh: 'center'

                        ClickableImage:
                            size_hint: None, None
                            source: "res/ic_minus.png"
                            width: 19
                            height: 19
                            allow_stretch: True
                            keep_ratio: True
                            pos_hint: {"center_y": .5}
                            on_release: app.config_temp_setting(decrease=True, param='max')

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
                        text_color: app.color_palette["blue"]
                        size_hint: 1, None
                        height: 64
                        on_release: app.sync_db_logs_thread(show_snackbar = True)

                    MDSeparator:

                    ClickableMDLabel:
                        text: "Export Logs"
                        halign: 'left'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: app.color_palette["blue"]
                        size_hint: 1, None
                        height: 64
                        on_release: 
                            app.show_export_dialog()

                    MDSeparator:

                    ClickableMDLabel:
                        text: "Clear Locally Stored Logs"
                        halign: 'left'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: app.color_palette["red"]
                        size_hint: 1, None
                        height: 64
                        on_release: app.wipe_local_logs(show_dialog=True)

                MDCard:
                    orientation: 'vertical'
                    size_hint: 1, None
                    height: 128
                    padding: [19, 12, 19, 8]

                    MDLabel:
                        text: "Minimum Prediction Score"
                        halign: 'left'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 24
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        size_hint_x: 0.5

                    MDBoxLayout:
                        orientation: 'horizontal'
                        size_hint: 1, None
                        height: 64
                        spacing: 8

                        Slider:
                            min: 70
                            max: 100
                            value: 85
                            step: 1
                            size_hint_x: 0.85
                            value_track: True
                            value_track_color: '#ffff00'
                            cursor_size: 64, 34
                            cursor_image: 'res/slider_cursor.png'
                            background_width: 0
                            on_value: app.config_rel_threshold(self, self.value)

                            canvas.before:
                                Color:
                                    rgba: 0.25, 0.25, 0.25, 1
                                Line:
                                    width: 4 
                                    cap: 'round'
                                    points: [self.x + self.padding, self.center_y, self.right - self.padding, self.center_y]

                        MDLabel:
                            id: rel_threshold_txt
                            text: f"{app.reliability_threshold*100}%"
                            halign: 'right'
                            font_name: "assets/sf_txt_reg.ttf"
                            font_size: 24
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1
                            size_hint_x: 0.15
                            pos_hint: {"center_y": .5}

                MDCard:
                    orientation: 'vertical'
                    size_hint: 1, None
                    height: self.minimum_height
                    padding: [19, 0, 19, 0]

                    MDBoxLayout:
                        orientation: 'horizontal'
                        size_hint: 1, None
                        height: 64
                        padding: [0, 12, 0, 12]

                        MDLabel:
                            text: "Capture Result"
                            halign: 'left'
                            pos_hint: {"center_y": .5}
                            font_name: "assets/sf_txt_reg.ttf"
                            font_size: 24
                            size_hint: 1, None
                            height: 64
                            size_hint_x: 1

                        ToggleSwitch:
                            on_release: app.toggle_capture_inf(self.active)
                            pos_hint: {"center_y": .5}

                    MDSeparator:

                    MDBoxLayout:
                        orientation: 'horizontal'
                        size_hint: 1, None
                        height: 64
                        padding: [0, 12, 0, 12]

                        ClickableMDLabel:
                            text: "Camera Resolution"
                            halign: 'left'
                            pos_hint: {"center_y": .5}
                            font_name: "assets/sf_txt_reg.ttf"
                            font_size: 24
                            size_hint: 1, None
                            height: 64
                            size_hint_x: 0.6
                            on_release: app.show_cam_res_dialog()

                        ClickableMDLabel:
                            id: txt_cam_res
                            text: f"{app.def_cam_res} at {app.cam_res[app.def_cam_res][2]} fps"
                            halign: 'right'
                            font_name: "assets/sf_txt_reg.ttf"
                            font_size: 24
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 0.5
                            size_hint_x: 0.4
                            on_release: app.show_cam_res_dialog()

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
                        text_color: app.color_palette["red"]
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

            SysIconButton:
                id: btn_bck_dashboard
                text: "Dashboard"
                icon: "res/ic_back.png"
                background_normal: "res/btn_pill_gray_s.png"
                background_down: "res/btn_pill_gray_s_down.png"
                on_release: app.go_to_dashboard()

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

            SysIconButton:
                id: logs_btn_bck_dashboard
                icon: "res/ic_sync.png"
                text: "Sync Logs"
                background_normal: "res/btn_pill_gray_s.png"
                background_down: "res/btn_pill_gray_s_down.png"
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

# ---------------------------------------------------FULL SCREEN---------------------------------------------------------
<FullScreen>:
    name: "full_view"

    RelativeLayout:
        size_hint: 1, 1

        Image:
            id: fullscreen_camfeed
            size_hint: 1, 1
            allow_stretch: True

        MDBoxLayout:
            id: fullscreen_batch_id_view
            orientation: "vertical"
            size_hint_x: 0.35
            # Let Kivy automatically wrap the box around the two text labels
            adaptive_height: True 
            pos_hint: {"top": 1.0, "center_x": 0.5}
            padding: [5, 5, 5, 5]
            spacing: 1

            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1 
                BorderImage:
                    source: 'res/btn_pill_gray_l.png'
                    pos: self.pos
                    size: self.size
                    border: [28, 28, 28, 28]
            MDLabel:
                id: id_batch_full_screen
                text: app.name_count_batch if app.name_count_batch else "Not Counting"
                font_name: "assets/sf_txt_bold.ttf"
                font_size: 22
                color: 1, 1, 1, 1
                shorten: True
                shorten_from: 'right'
                halign: "center"
                adaptive_height: True

            MDLabel:
                text: "BATCH"
                font_name: "assets/sf_txt_reg.ttf"
                font_size: 18
                color: 1, 1, 1, 1
                halign: "center"
                # adaptive_height forces the label to snap to the text, 
                # avoiding overlap with the label below it.
                adaptive_height: True
        MDBoxLayout:
            size_hint: 0.5, None
            padding: [12]
            pos_hint: {"top":1.0, "x":0.5}
            orientation: "horizontal"
            height: self.minimum_height
            spacing: 19
            halign: "right"

            Widget:
                size_hint: 1, 1

            SysIconButton:
                id: minimize
                icon: "res/ic_minimize_s.png"
                text: "Minimize"
                background_normal: "res/btn_pill_gray_s.png"
                background_down: "res/btn_pill_gray_s_down.png"
                on_release: app.go_to_dashboard()
                size_hint: None, None
# --------------------------------------------------CUSTOM CLASSES-------------------------------------------------------
<Snackbar>:
    id: snackbar
    orientation: "horizontal"
    size_hint_y: None
    height: 48
    adaptive_width: True 
    opacity: 0
    pos_hint: {"center_x": 0.5, "center_y": 0.05} 
    spacing: 10
    padding: [16, 0, 16, 0]
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
        source: 'res/ic_warning_s.png' if root.warning_mode else 'res/ic_info_s.png'
        width: 26
        height: 26
        allow_stretch: True
        keep_ratio: True
        pos_hint: {"center_y": .5}
    
    MDLabel:
        id: toast_text
        text: ""
        font_name: 'assets/sf_txt_reg.ttf'
        font_size: 20
        theme_text_color: "Custom"
        text_color: (1, 1, 1, 1) if root.warning_mode else (0, 0, 0, 1)
        halign: 'left'
        valign: 'center'
        adaptive_width: True

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

<ExportLogsDialog>
    width: 500
    height: 380
    size_hint: None, None
    background: ''
    background_color: 0, 0, 0, 0
    separator_height: 0
    title: ""
    command_on_proceed: app.export_logs
    auto_dismiss: False
    palette: app.color_palette

    MDBoxLayout:
        orientation: 'vertical'
        size_hint: 1, None
        height: 380
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
                text: "Export Logs via Email"
                font_name: "assets/sf_txt_bold.ttf"
                font_size: 24
                text_color: 1, 1, 1, 1
                size_hint_x: 1
                halign: 'left'

            MDLabel:
                text: "Logs are exported in csv format. Enter email address and pick range of to export."
                font_name: "assets/sf_txt_reg.ttf"
                font_size: 20
                text_color: 1, 1, 1, 1
                size_hint_x: 1
                halign: 'left'

        MDBoxLayout:
            orientation: 'vertical'
            size_hint: 1, None
            height: 72
            spacing: 12

            TextInput:
                id: input_email
                hint_text: "Email Address"
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
                height: self.minimum_height
                padding: [12, 0, 12, 0]
                spacing: 12

                MDCard:
                    id: opt_1
                    orientation: 'horizontal'
                    size_hint: 1, None
                    spacing: 19
                    height: 48
                    radius: [24]

                    ClickableMDLabel:
                        text: "Last Week"
                        halign: 'center'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 20
                        size_hint: 1, None
                        height: 48
                        on_release: root.set_timerange("opt_1")

                MDCard:
                    id: opt_2
                    orientation: 'horizontal'
                    size_hint: 1, None
                    spacing: 19
                    height: 48
                    radius: [24]

                    ClickableMDLabel:
                        text: "Last Month"
                        halign: 'center'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 20
                        size_hint: 1, None
                        height: 48
                        on_release: root.set_timerange("opt_2")

                MDCard:
                    id: opt_3
                    orientation: 'horizontal'
                    size_hint: 1, None
                    spacing: 19
                    height: 48
                    radius: [24]

                    ClickableMDLabel:
                        text: "All time"
                        halign: 'center'
                        font_name: "assets/sf_txt_reg.ttf"
                        font_size: 20
                        size_hint: 1, None
                        height: 48
                        on_release: root.set_timerange("opt_3")

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
                text: "EXPORT"
                size_hint: 1, None
                height: 56
                font_size: 24
                font_name: "assets/sf_txt_bold.ttf"
                background_normal: "res/btn_pill_blue_l.png"
                background_down: "res/btn_pill_blue_l_down.png"
                on_release: root.execute_proceed(root.ids.input_email.text, root.input_timerange)

<CamResDialog>
    width: 500
    height: 390
    size_hint: None, None
    background: ''
    background_color: 0, 0, 0, 0
    separator_height: 0
    title: ""
    command_on_proceed: app.config_cam_res
    auto_dismiss: False
    palette: app.color_palette
    default_opt: app.def_cam_res

    MDBoxLayout:
        orientation: 'vertical'
        size_hint: 1, None
        height: 400
        spacing: 19
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
                text: "Change Camera Resolution"
                font_name: "assets/sf_txt_bold.ttf"
                font_size: 24
                text_color: 1, 1, 1, 1
                size_hint_x: 1
                halign: 'left'

            MDLabel:
                text: "Higher resolution results to lower frame rate but gives you higher quality images."
                font_name: "assets/sf_txt_reg.ttf"
                font_size: 20
                text_color: 1, 1, 1, 1
                size_hint_x: 1
                halign: 'left'
                height: self.texture_size[1]

            MDCard:
                id: opt_1
                orientation: 'vertical'
                size_hint: 1, None
                height: 48
                padding: [12, 0, 12, 0]
                radius: [24]
                on_release: root.select("opt_1")
                
                MDLabel:
                    text: "4K at 10fps"
                    font_name: "assets/sf_txt_reg.ttf"
                    font_size: 20
                    text_color: 1, 1, 1, 1
                    size_hint_x: 1
                    halign: 'center'

            MDCard:
                id: opt_2
                orientation: 'vertical'
                size_hint: 1, None
                height: 48
                padding: [12, 0, 12, 0]
                radius: [24]
                on_release: root.select("opt_2")
                
                MDLabel:
                    text: "2K at 15fps"
                    font_name: "assets/sf_txt_reg.ttf"
                    font_size: 20
                    text_color: 1, 1, 1, 1
                    size_hint_x: 1
                    halign: 'center'

            MDCard:
                id: opt_3
                orientation: 'vertical'
                size_hint: 1, None
                height: 48
                padding: [12, 0, 12, 0]
                radius: [24]
                on_release: root.select("opt_3")
                
                MDLabel:
                    text: "1080p at 20fps"
                    font_name: "assets/sf_txt_reg.ttf"
                    font_size: 20
                    text_color: 1, 1, 1, 1
                    size_hint_x: 1
                    halign: 'center'

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
                text: "SAVE"
                size_hint: 1, None
                height: 56
                font_size: 24
                font_name: "assets/sf_txt_bold.ttf"
                background_normal: "res/btn_pill_blue_l.png"
                background_down: "res/btn_pill_blue_l_down.png"
                on_release: root.execute_proceed(root.selected_opt)

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

<ToggleSwitch>:
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
        spacing: 12

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

    #    SysIconButton:
    #        icon: "res/ic_image.png"
    #        text: "See Results"
    #        background_normal: "res/btn_pill_gray_s.png"
    #        background_down: "res/btn_pill_gray_s_down.png"

        SysIconButton:
            icon: "res/ic_trash_s.png"
            background_normal: "res/btn_pill_gray_s.png"
            background_down: "res/btn_pill_gray_s_down.png"
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
        text: f"[font=assets/sf_mono_reg.otf][color=#ffffff]OPERATOR: [/font][/color][font=assets/sf_mono_reg.otf][color=#0078ff]{root.log_name_op}[/font][/color]"

    MDLabel:
        markup: True
        size_hint_x: 1
        size_hint_y: None
        height: self.texture_size[1]
        font_size: 24
        halign: 'left'
        text: f"[font=assets/sf_mono_reg.otf][color=#ffffff]PL COUNT: [/font][/color][font=assets/sf_mono_reg.otf][color=#0078ff]{root.log_pl_count}[/font][/color]"

    MDLabel:
        markup: True
        size_hint_x: 1
        size_hint_y: None
        height: self.texture_size[1]
        font_size: 24
        halign: 'left'
        text: f"[font=assets/sf_mono_reg.otf][color=#ffffff]SUB-BATCHES: [/font][/color][font=assets/sf_mono_reg.otf][color=#0078ff]{root.log_num_sbatches}[/font][/color]"    

    MDLabel:
        markup:True
        size_hint_x: 1
        size_hint_y: None
        height: self.texture_size[1]
        font_size: 24
        halign: 'left'
        text: f"[font=assets/sf_mono_reg.otf][color=#ffffff]RELIABILITY SCORE: [/font][/color][font=assets/sf_mono_reg.otf][color=#db3838]{root.log_margin_of_err:.2f}[/font][/color]"

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

<SysIconButton>:
    orientation: 'horizontal'
    size_hint_x: None
    height: 36
    width: content_box.width + 5 if self.text else content_box.width

    background_normal: "res/btn_pill_gray_s.png"
    background_down: "res/btn_pill_gray_s_down.png"
    
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        BorderImage:
            pos: self.pos
            size: self.size
            source: root.background_down if self.state == 'down' else root.background_normal
            border: [18, 18, 18, 18]

    BoxLayout:
        id: content_box
        orientation: 'horizontal'
        size_hint_x: None
        width: self.minimum_width
        spacing: 5 if root.text else 0
        padding: [6, 0, 6, 0]

        Image:
            source: root.icon
            size_hint: None, None
            size: 24, 24
            pos_hint: {'center_y': .5}
            allow_stretch: True

        Label:
            id: label_id
            text: root.text
            font_size: 18
            font_name: "assets/sf_txt_reg.ttf"
            halign: 'left'
            valign: 'center'
            size_hint_x: None
            text_size: None, self.height
            width: self.texture_size[0]
'''
def smooth_anim_curve(t):
    """Smooth anumation curve based on the Cubic Bézier curve"""
    p1x, p1y = 0.01, 1.0
    p2x, p2y = 0.1, 1.2
    u = t
    for _ in range(5):
        current_x = 3 * (1 - u)**2 * u * p1x + 3 * (1 - u) * u**2 * p2x + u**3
        dx = 3 * (1 - u)**2 * p1x + 6 * (1 - u) * u * (p2x - p1x) + 3 * u**2 * (1 - p2x)
        if abs(dx) < 1e-6:
            break
        u -= (current_x - t) / dx
        u = max(0.0, min(1.0, u))
    return 3 * (1 - u)**2 * u * p1y + 3 * (1 - u) * u**2 * p2y + u**3

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
        Clock.schedule_interval(self.update_clock, 1)

    def update_clock(self, *args):
        """Fetches and formats the current time, updating the UI label."""
        now = datetime.now()
        month = now.strftime('%b').upper()
        time_str = now.strftime('%I:%M %p').lstrip('0') 
        formatted_time = f"{month} {now.day}, {now.year} | {time_str}"
        
        if 'clock_label' in self.ids:
            self.ids.clock_label.text = formatted_time

    def on_pre_leave(self, *args):
        # Lock the feed the millisecond before the slide begins
        app = MDApp.get_running_app()
        app.is_transitioning = True

    def on_enter(self, *args):
        # Unlock the feed the millisecond the slide finishes
        app = MDApp.get_running_app()
        app.is_transitioning = False

class SettingsScreen(Screen):
    pass

class LogsScreen(Screen):
    pass

class FullScreen(Screen):
    def on_pre_leave(self, *args):
        # Lock the feed the millisecond before sliding down
        app = MDApp.get_running_app()
        app.is_transitioning = True

    def on_enter(self, *args):
        # Unlock the feed the millisecond the slide finishes
        app = MDApp.get_running_app()
        app.is_transitioning = False

class UlangSystemApp(MDApp):
    is_transitioning = BooleanProperty(False) # A page is actively transitioning

    # SYSTEM STATUS
    count_active = BooleanProperty(False) # For switching UI interface mode
    is_counting = BooleanProperty(False) # Inference active state
    is_cam_initializing = BooleanProperty(False)
    active_alert = BooleanProperty(False)
    empty_chamber = True
    critical_temp = BooleanProperty(False)
    critical_load = BooleanProperty(False)
    monitoring_freezed = BooleanProperty(False) # Set to True if chamber condition is non-critical or currently timed out
    
    alert_msg = {
        'CRITICAL_TEMP':"Water temperature exceeds acceptable level. Counting process is temporarily paused.",
        'CRITICAL_LOAD':"Water level is too high. Please reduce water from the container."
    }
    
    # Connectivity Status
    is_online = BooleanProperty(False)
    wifi_on = BooleanProperty(False)
    wifi_stat = ['disconnected', '1', '2', '3', '4']
    wifi_strength = NumericProperty(0)

    # YOLO model path
    model_path = 'ulangn-obb-annotator-v6-4_ncnn_model'

    # UI Elements
    dialog = None
    snackbar = None
    current_active_widget = ObjectProperty(None, allownone=True)
    color_palette = {
        "red":'#db3838',
        "blue":'#0078ff',
        "green":'#38db5c',
        "yellow":'#ccba00',
        "dark_gray":'#2e2e2e',
        "dark_blue":'#0000a2'
        }

    # Settings
    capture_inf = BooleanProperty(False)
    timeout_scan = NumericProperty(10)
    def_cam_res = OptionProperty("4K", options=["4K", "2K", "1080p"])
    cam_res = {
        "4K" : [4608, 2592, 9],
        "2K" : [2304, 1296, 15],
        "1080p" : [1920, 1080, 18] } # Values are in [W, H, fps] format
    
    min_temp = 27.0
    max_temp = 31.0
    max_load = 5.2 #In kilograms
    sub_optimal_temp = [23.2, 37]

    # Placeholders
    sub_batch_history = {}
    name_count_batch = ""
    name_operator = ""
    total_batches_created = NumericProperty(0)
    total_count = NumericProperty(0)
    reliability_score = ObjectProperty(0.0)
    reliability_threshold = ObjectProperty(0.8)
    reliability_scores = []
    water_vol = NumericProperty(0.0)
    water_vol_array = []
    water_temp = NumericProperty(0.0)
    water_temp_array = []
    count_timer = NumericProperty(0.0)
    count_timer_array = []
    batch_uuid = StringProperty("")

    payload = {
            "local_id": None, #Auto-generated uuid
            "timestamp": None,
            "batch_id": None,
            "op_name": None,
            "count_total_pl": None,
            "num_sbatch": None,
            "count_per_sbatch": None,
            "model_version": None,
            "rel": None,
            "ave_temp": None,
            "ave_approx_density": None,
            "time_elapsed": None
        }

    frame_bytes=ObjectProperty(None,allownone=True)

    # Online Database: Supabase Client
    SUPABASE_API_URL = 'https://nltmvrjxasslpqbdyamg.supabase.co'
    SUPABASE_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5sdG12cmp4YXNzbHBxYmR5YW1nIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MzYyNzA3NSwiZXhwIjoyMDk5MjAzMDc1fQ.u3AtVGmKXwP9r9JfvfpVrvcRdZZ7ujskrE5tFM1ZdoU'

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

        try:
            self.arduino = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
            time.sleep(2)
            print("[INFO] Arduino Active via UART")

        except Exception as e:
            self.arduino = None
            print(f"[WARNING] Arduino Unavailable: {e}")

        Window.bind(on_key_down=self.on_keyboard_down)
        return Builder.load_string(INTERFACE)

    def on_start(self):
        """Called automatically after the app builds."""
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
            self.btn_home.when_pressed = lambda: Clock.schedule_once(self.go_to_dashboard)

            self.btn_start = HardwareButton(22)
            self.btn_start.when_pressed = lambda: Clock.schedule_once(self.start_batch_count)

        # Initialize camera
        self.start_camera_loading()

        # Initialize Raspi-Arduino Listener
        listener = threading.Thread(target=self.listen_to_ard, daemon=True)
        listener.start()

    # [SECTION] Arduino-Raspi Communication Protocol
    @mainthread
    def update_sensor_reads(self, data):
        """@mainthread: Updates the screen with the JSON data from the Arduino"""
        wtrlvl = data.get('wtrlvl')
        wtrtemp = data.get('temp')
        self.root.ids.dashboard_screen.ids.water_temp_label.text = f"{wtrtemp} °C"
        self.root.ids.dashboard_screen.ids.water_lvl_label.text = f"{wtrlvl} cm"

        if not wtrtemp=='--':
            self.water_temp = float(wtrtemp)

            if self.count_active:
                self.water_temp_array.append(wtrtemp)

        if not wtrlvl=="--":
            #Calculate the water volume here, output in liters (L)
            wtrvol = (34 * 19 * float(wtrlvl))/1000
            self.water_vol = wtrvol

            if self.count_active:
                self.water_vol_array.append(wtrvol)
            
            self.root.ids.dashboard_screen.ids.water_vol_label.text = f"{wtrvol:.2f} L"

        else:
            wtrvol="--"
            self.root.ids.dashboard_screen.ids.water_vol_label.text = f"{wtrvol} L"

        if self.water_temp < self.min_temp or self.water_temp > self.max_temp:
            self.critical_temp = True
        else: 
            self.critical_temp = False

        if wtrvol > self.max_load:
            self.critical_load = True

        else:
            self.critical_load = False

        if self.is_counting and (self.water_temp < self.min_temp or self.water_temp > self.max_temp):
            self.remove_sub_batch(self.current_active_widget, show_dialog=False)
            self.total_batches_created -= 1
            Clock.schedule_once(lambda dt: self.show_snackbar(warning_mode = True, message="Warning: Water temperature on critical level!"))
            self.is_counting=False

        if self.is_counting and (wtrvol > self.max_load):
            self.remove_sub_batch(self.current_active_widget, show_dialog=False)
            self.total_batches_created -= 1
            Clock.schedule_once(lambda dt: self.show_snackbar(warning_mode = True, message="Warning: Water level on critical level!"))
            self.is_counting=False

    def listen_to_ard(self):
        """
        @bgthread: Pings the controller for sensor readings
        """
        while True:
            if self.arduino:
                # Ping the Arduino for the latest sensor readings
                ping_cmd = json.dumps({"command": "get_sensors"}) + "\n"
                self.arduino.write(ping_cmd.encode('utf-8'))
                
                # MCU response wait
                time.sleep(0.1)
                
                # Read the incoming response
                if self.arduino.in_waiting > 0:
                    try:
                        raw_data = self.arduino.readline().decode('utf-8').strip()
                        sensor_data = json.loads(raw_data)
                        self.update_sensor_reads(sensor_data)
                        print(f"[Sensors Updated] Temp: {sensor_data.get('temp')}°C, Lvl: {sensor_data.get('wtrlvl')}")
                        
                    except json.JSONDecodeError:
                        print("Failed to decode JSON from Arduino.")
            else:
                sensor_data = {"temp":"--", "wtrlvl":"--"}
                self.update_sensor_reads(sensor_data)
            
            # Polling delay dictates how fast the ping-pong cycle runs
            time.sleep(1.0)

    def talk_to_ard(self, action):
        """
        Triggered by the Main UI Thread when a technician taps a Kivy button.
        """
        try:
            command_dict = {"command": action}
            
            # Convert Python dictionary to JSON string and add the newline delimiter
            json_string = json.dumps(command_dict) + "\n"
            
            # Send it down the USB wire
            self.arduino.write(json_string.encode('utf-8'))
            print(f"Sent command to Arduino: {action}")

        except:
            self.show_snackbar(message="Warning: Crontroller is unavailable", warning_mode=True)
            print("[Error] Arduino is not responding")

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

    # [SECTION] Camera and Image Processing and AI Inference Pipeline
    def start_camera_loading(self, anti_loop:bool = False, *args):
        """Resets the UI and spawns the background worker."""
        dashboard_screen = self.root.ids.dashboard_screen
        camfeed = self.root.ids.dashboard_screen.ids.camfeed_pane

        if not self.monitoring_freezed:
            # Checks the temperature and water level first before loading the camera if alert is not timed out
            if not anti_loop:
                self.check_chamber_stat(0)
        
        else:
            # If checking is queued, temporarily disable the alert
            self.active_alert = False
        
        if self.active_alert:
            if self.critical_temp:
                if self.critical_load:
                    camfeed.current = "camfeed_alert_screen"
                    dashboard_screen.ids.ic_alert.source = 'res/ic_water_level.png'
                    dashboard_screen.ids.txt_alert_title.text = "Critical Water Level"
                    dashboard_screen.ids.txt_alert_message.text = self.alert_msg["CRITICAL_LOAD"]

                else:  
                    camfeed.current = "camfeed_alert_screen"
                    dashboard_screen.ids.ic_alert.source = 'res/ic_temperature.png'
                    dashboard_screen.ids.txt_alert_title.text = "Critical Temperature"
                    dashboard_screen.ids.txt_alert_message.text = self.alert_msg["CRITICAL_TEMP"]

        else:
            if hasattr(self, 'picam2') or self.is_cam_initializing:
                return
            self.is_cam_initializing = True
            self.root.ids.dashboard_screen.ids.camfeed_pane.current = "camfeed_loading_screen"
            threading.Thread(target=self._init_hardware, daemon=True).start()

    def _init_hardware(self):
        """@backgroundthread: Initializes capturing and loading AI model"""
        try:
            self.picam2 = Picamera2()
            vd_config = self.picam2.create_video_configuration(
                main={"size": (self.cam_res[self.def_cam_res][0], self.cam_res[self.def_cam_res][1]), "format": "RGB888"}
            )
            self.picam2.configure(vd_config)
            self.picam2.start_preview(Preview.NULL)
            self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
            self.picam2.start()
            
            self.model = YOLO(self.model_path)
            
            # Initialize Fuzzy Evaluation
            self.fuzzy_sim = self.init_fuzzy()
            self.prev_count = 0 
            
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
        """@backgroundthread: Grabs camera live feed frames, runs inference, 
        initializes fuzzy logic, and passes the output to UI when reliability 
        score threshold is met."""

        targ_fps = self.cam_res[self.def_cam_res][2]
        targ_frame_time = 1/targ_fps

        while True:
            sttime = time.time()
            hi_res_frame = self.picam2.capture_array()
            
            try:
                if self.is_counting:
                    inf_result = self.model.predict(hi_res_frame, conf=0.35, verbose=False)

                    if inf_result[0].obb is not None:
                        inf_count = len(inf_result[0].obb)
                        
                        # Crisp Values Extraction
                        # Mean Confidence
                        confs = inf_result[0].obb.conf.cpu().numpy()
                        c_mean = confs.mean() if len(confs) > 0 else 0.0
                        
                        # Temporal Variance (Percentage)
                        v_temp = abs(inf_count - self.prev_count) / max(self.prev_count, 1)
                        v_temp = min(v_temp, 1.0) # Cap at 100%

                        # Clumping Index (Density Proxy)
                        c_index = 0.0
                        if inf_count > 1:
                            # Extract normalized corner points (xyxyxyxyn)
                            corners = inf_result[0].obb.xyxyxyxyn.cpu().numpy()
                            pred_polys = [Polygon(c) for c in corners]
                            
                            area_total = sum(p.area for p in pred_polys)
                            if area_total > 0:
                                area_union = unary_union(pred_polys).area
                                c_index = max(0.0, min(1.0 - (area_union / area_total), 1.0)) 
                        
                        # Fuzzy Evaluation
                        self.fuzzy_sim.input['confidence'] = c_mean
                        self.fuzzy_sim.input['clumping'] = c_index
                        self.fuzzy_sim.input['variance'] = v_temp
                        self.fuzzy_sim.compute()
                        
                        try:
                            self.fuzzy_sim.compute()
                            frame_reliability = self.fuzzy_sim.output['reliability']

                        except KeyError:
                            # Safeguard from KeyError
                            frame_reliability = 0.0
                        print(f"[FUZZY] Conf: {c_mean:.2f} | Clump: {c_index:.2f} | Var: {v_temp:.2f} | Rel: {frame_reliability:.2f}")

                        # Count locking mechanism
                        if frame_reliability >= self.reliability_threshold:
                            if self.capture_inf:
                                # directory for the export
                                save_dir = f"res_captured/{self.batch_uuid}"
                                os.makedirs(save_dir, exist_ok=True)
                                base_path = os.path.join(save_dir, f"{self.batch_uuid}_SB{self.total_batches_created}")
                                
                                # RAW Image
                                # The camera captures in RGB888, but OpenCV's imwrite requires BGR
                                # bgr_frame = cv2.cvtColor(hi_res_frame, cv2.COLOR_RGB2BGR)
                                cv2.imwrite(f"{base_path}.jpg", hi_res_frame)
                                
                                # YOLO-OBB annotations (.txt)
                                with open(f"{base_path}.txt", "w") as f:
                                    classes = inf_result[0].obb.cls.cpu().numpy()
                                    norm_corners = inf_result[0].obb.xyxyxyxyn.cpu().numpy()
                                    
                                    for i in range(inf_count):
                                        cls_id = int(classes[i])
                                        c = norm_corners[i] # Extracts the 4 [x,y] points for the current box
                                        
                                        # Format: class_id x1 y1 x2 y2 x3 y3 x4 y4
                                        f.write(f"{cls_id} {c[0][0]:.6f} {c[0][1]:.6f} {c[1][0]:.6f} {c[1][1]:.6f} {c[2][0]:.6f} {c[2][1]:.6f} {c[3][0]:.6f} {c[3][1]:.6f}\n")
                                
                                print(f"[LOG] Saved captured results to {base_path}")

                            # Safely hand the final count back to the Main UI Thread
                            Clock.schedule_once(lambda dt, count=inf_count: self._lock_sub_batch(count))
                            self.is_counting = False # Stop inference loop for this sub-batch
                            self.reliability_score = frame_reliability
                            self.reliability_scores.append(self.reliability_score)

                        self.prev_count = inf_count

                    else:
                        inf_count = 0
                        self.prev_count = 0

                    inf_wframe = inf_result[0].plot(labels=False, line_width=2, conf=False)
                    disp_frame = cv2.resize(inf_wframe, (434, 244), interpolation=cv2.INTER_LINEAR)

                else:
                    disp_frame = cv2.resize(hi_res_frame, (434, 244), interpolation=cv2.INTER_LINEAR)

                rgb_frame = cv2.cvtColor(disp_frame, cv2.COLOR_BGR2RGB)
                self.frame_bytes = rgb_frame.tobytes()

                if not self.is_transitioning:
                    h = 400 if self.root.current == "full_view" else 244
                    w = 800 if self.root.current == "full_view" else 434
                    self.update_feed(self.frame_bytes, w, h, inf_count if self.is_counting else 0)
                    
                eltime = time.time() - sttime
                self.count_timer += eltime
                slptime = targ_frame_time - eltime

                if slptime > 0:
                    time.sleep(slptime)

            except Exception as e:
                print(f"[DEBUG] {e}")
                traceback.print_exc()

    @mainthread
    def update_feed(self, frame_bytes, width, height, total_count, *args):
        """@mainthread: Refresh camera_feed"""
        
        if self.is_transitioning:
            return

        try:
            texture = Texture.create(size=(width, height), colorfmt='rgb')
            texture.blit_buffer(frame_bytes, colorfmt='rgb', bufferfmt='ubyte')
            texture.flip_vertical()

            cam_widget_main = self.root.ids.dashboard_screen.ids.camera_feed
            cam_widget_full = self.root.ids.full_view.ids.fullscreen_camfeed

            if self.root.current == "dashboard":
                if cam_widget_main:
                    cam_widget_main.texture = texture
                    cam_widget_main.canvas.ask_update()
            elif self.root.current == "full_view":
                if cam_widget_full:
                    cam_widget_full.texture = texture
                    cam_widget_full.canvas.ask_update()

        except Exception as tex_err:
            print(f"[Texture Debug Error] Bypassed context error: {tex_err}")

        predict_count_txt = self.root.ids.dashboard_screen.ids.camfeed_count
        predict_count_txt.text = str(total_count) if total_count > 0 else "--"

        if self.is_counting:
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

    def init_fuzzy(self):
        confidence = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'confidence')
        clumping = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'clumping') 
        variance = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'variance')
        reliability = ctrl.Consequent(np.arange(0, 1.01, 0.01), 'reliability')

        # Fuzzy MFs
        confidence['poor'] = fuzz.trapmf(confidence.universe, [0, 0, 0.77, 0.80])
        confidence['acceptable'] = fuzz.trimf(confidence.universe, [0.78, 0.81, 0.84])
        confidence['high'] = fuzz.trapmf(confidence.universe, [0.82, 0.84, 1.0, 1.0])
    
        # MFs for Clumping
        clumping['sparse'] = fuzz.trapmf(clumping.universe, [0, 0, 0.1, 0.2])
        clumping['moderate'] = fuzz.trimf(clumping.universe, [0.015, 0.06, 0.12])
        clumping['dense'] = fuzz.trapmf(clumping.universe, [0.1, 0.15, 1.0, 1.0])
    
        # MFs for Temporal Variance
        variance['stable'] = fuzz.trapmf(variance.universe, [0, 0, 0.05, 0.07])
        variance['jittery'] = fuzz.trimf(variance.universe, [0.05, 0.07, 0.10])
        variance['erratic'] = fuzz.trapmf(variance.universe, [0.08, 0.10, 1.0, 1.0])

        # Output MFs
        reliability['unacceptable'] = fuzz.trapmf(reliability.universe, [0, 0, 0.4, 0.6])
        reliability['acceptable'] = fuzz.trimf(reliability.universe, [0.55, 0.7, 0.85])
        reliability['excellent'] = fuzz.trapmf(reliability.universe, [0.75, 0.85, 1.0, 1.0])

        # Conditions for 'excellent' reliability
        rule1 = ctrl.Rule(
                        (confidence['high'] | confidence['acceptable']) & variance['stable'] & (clumping['sparse'] | clumping['moderate']), 
                        reliability['excellent']
                    )
        
        #Conditions for 'acceptable' reliability
        rule2 = ctrl.Rule(
                    (confidence['high'] | confidence['acceptable']) & variance['jittery'] & (clumping['sparse'] | clumping['moderate']), 
                    reliability['acceptable']
                )
        rule3 = ctrl.Rule(
                    (confidence['high'] | confidence['acceptable']) & variance['stable'] & clumping['dense'], 
                    reliability['acceptable']
                )
        
        #Conditions for 'unacceptable' reliability
        rule4 = ctrl.Rule(
                    (confidence['acceptable'] | confidence['poor']) & (variance["jittery"] | variance['erratic']) & (clumping['moderate'] | clumping['dense']),
                    reliability['unacceptable']
                )
    
        rule5 = ctrl.Rule(
                    confidence['poor'] | variance['erratic'], 
                    reliability['unacceptable']
                )

        judge_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5])
        return ctrl.ControlSystemSimulation(judge_ctrl)

    # [SECTION] Settings Commands
    def config_temp_setting(self, input:bool=False, increase:bool=False, decrease:bool=False, param:str='', *args):
        input_max = self.root.ids.settings_screen.ids.input_max_temp
        input_min = self.root.ids.settings_screen.ids.input_min_temp

        if increase:
            if param=="min":
                if self.max_temp > self.min_temp+1:
                    self.min_temp += 1
                    input_min.text = str(self.min_temp)

                else: 
                    self.show_snackbar(message="Temperature range will be too small", warning_mode=True)
                
            elif param=="max":
                if self.max_temp+1 <= self.sub_optimal_temp[1]:
                    self.max_temp += 1
                    input_max.text = str(self.max_temp)

                else:
                    self.show_snackbar(message="Maximum temperature out sub-optimal of range", warning_mode=True)

        elif decrease:
            if param=="min":
                if self.min_temp-1 >= self.sub_optimal_temp[0]:
                    self.min_temp -= 1
                    input_min.text = str(self.min_temp)

                else:
                    self.show_snackbar(message="Minimum temperature out of sub-optimal range", warning_mode=True)

            elif param=="max":
                if (self.max_temp-1) > self.min_temp:
                    self.max_temp -= 1
                    input_max.text = str(self.max_temp)

                else:
                    self.show_snackbar(message="Temperature range will be too small", warning_mode=True)

        elif input:
            float_input = float(input_max.text) if param=="max" else float(input_min.text)

            if param=="min":
                if float_input <= self.max_temp-1:
                    if float_input > self.sub_optimal_temp[0]:
                        self.min_temp = float_input

                    else:
                        input_min.text = str(self.min_temp)
                        self.show_snackbar(message="Minimum temperature out of sub-optimal range", warning_mode=True)

                elif float_input > self.max_temp:
                    input_min.text = str(self.min_temp)
                    self.show_snackbar(message="Invalid input", warning_mode=True)

                else:
                    input_min.text = str(self.min_temp)
                    self.show_snackbar(message="Temperature range will be too small", warning_mode=True)  

            elif param=="max": 
                if float_input >= self.min_temp+1:
                    if float_input <= self.sub_optimal_temp[1]:
                        self.max_temp = float_input

                    else:
                        input_max.text = str(self.max_temp)
                        self.show_snackbar(message="Maximum temperature out of sub-optimal range", warning_mode=True)

                elif float_input < self.min_temp:
                    input_max.text = str(self.max_temp)
                    self.show_snackbar(message="Invalid input", warning_mode=True)

                else:
                    self.max_temp = self.min_temp+1
                    input_max.text = str(self.max_temp)
                    self.show_snackbar(message="Temperature range will be too small", warning_mode=True)
                    
    def config_rel_threshold(self, instance, slider_value):
        """Adjust reliability score threshold."""
        self.reliability_threshold = int(slider_value)/100
        rel_percent = self.reliability_threshold*100
        self.root.ids.settings_screen.ids.rel_threshold_txt.text = f"{rel_percent}%"

    def toggle_capture_inf(self, value):
        if value:
            self.capture_inf = False
        else: 
            self.capture_inf = True

    # [SECTION] Wifi Configuration Commands
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
            for line in result.split('\n'):
                if line.startswith('yes'):
                    parts = line.split(':')
                    return {
                        "connected": True, 
                        "ssid": parts[1], 
                        "strength": int(parts[2])
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
            self.is_transitioning = True
            if self.root.current == "full_view":
                self.root.transition.direction = "down"
            else:
                self.root.transition.direction = "right"
            self.root.current = "dashboard"
            Clock.schedule_once(self._unlock_feed, 0.7)
        self.start_camera_loading()

    def go_full_view(self, *args):
        if self.root.current != "full_view":
            self.is_transitioning = True
            self.root.transition.direction = "up"
            self.root.current = "full_view"
            Clock.schedule_once(self._unlock_feed, 0.5)

    def _unlock_feed(self, dt):
        """Re-enables the live camera feed after a screen transition."""
        self.is_transitioning = False

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

    def show_export_dialog(self, *args):
        self.popup = Factory.ExportLogsDialog()
        self.popup.open()

    def show_cam_res_dialog(self, *args):
        self.popup = Factory.CamResDialog()
        self.popup.open()

    # =============================================================================================================================

    def activate_count(self, input_name_batch = "", input_name_op = "", *args):
        self.name_count_batch = input_name_batch
        self.name_operator = input_name_op
    
        def execute_activation():
            self.count_active = True
            print('[INFO] Counting Process Activated')
            self.batch_uuid = str(uuid.uuid4())
            self.popup.dismiss()
            if self.aerator.is_active:
                self.talk_to_ard("aerator_off")
                self.aerator.is_active = False
            self.aerator.is_toggleable = False
            self.led_panels.is_active = True
            self.talk_to_ard("led_on")
            self.led_panels.is_toggleable = False
            self.right_pane.current = "panel_count_active"
            self.btm_btn.current = "btn_count_active"
            self.root.ids.dashboard_screen.ids.id_batch_camfeed.text = f"BATCH: {self.name_count_batch}"
            print(f"[INFO] Count started for: {self.name_count_batch}. Operator: {self.name_operator}")

        if not (self.name_count_batch and self.name_operator):
            self.show_snackbar(warning_mode=True, message="Batch detail entries are required.")
        else:
            execute_activation()

    # dev: checked, it: 01
    def deactivate_count(self, abort = False, *args):
        def execute_deactivation():
            self.count_active = False
            print('[INFO] Counting Process Deactivated')
            
            # Reset Status
            self.aerator.is_toggleable = True
            self.led_panels.is_toggleable = True
            
            # Reset Containers
            self.right_pane.current = "panel_count_inactive"
            self.btm_btn.current = "btn_count_inactive"
            self.sub_batch_scrollview.clear_widgets()
            
            # Clear Placeholders and Payload
            self.sub_batch_history.clear()
            self.total_count = 0
            self.total_batches_created = 0
            self.reliability_score = 0
            self.name_count_batch = ""
            self.name_operator = ""
            self.reliability_scores.clear()
            self.water_vol = 0
            self.water_vol_array = []
            self.water_temp = 0
            self.water_temp_array = []
            self.count_timer = 0
            self.count_timer_array = []
            self.payload.update({
                "local_id": None,
                "timestamp": None,
                "batch_id": None,
                "op_name": None,
                "count_total_pl": None,
                "num_sbatch": None,
                "count_per_sbatch": None,
                "model_version": None,
                "rel": None,
                "ave_temp": None,
                "ave_approx_density": None,
                "time_elapsed":None
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
            t=smooth_anim_curve
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
            t="in_back"
        )

        # Completely remove it from the Window memory when done
        anim_out.bind(on_complete=lambda *args: Window.remove_widget(self.snackbar))
        anim_out.start(self.snackbar)

    # dev: checked, it: 01
    @mainthread
    def _lock_sub_batch(self, locked_count):
        """Called by the background fuzzy evaluator when an Excellent frame is found."""
        if self.current_active_widget:
            #Append time elapsed and reset timer
            self.count_timer_array.append(self.count_timer)
            self.count_timer = 0

            self.current_active_widget.count = locked_count
            self.current_active_widget.is_active = False
            self.total_count += locked_count
            self.sub_batch_history[self.current_active_widget.batch_name] = locked_count
            self.current_active_widget = None
            
            # Provide visual feedback to the operator
            self.show_snackbar(message=f"PL Count: {locked_count}", warning_mode=False)

    #dev: checked, it: 01
    def count_on_click(self):
        """Triggered when the operator taps +SUB-BATCH. The AI handles the rest."""
        if not self.is_counting:
            # STATE 1: ADDING A SUB-BATCH
            self.is_counting = True
            
            # Reset prev_count so variance evaluates purely on this new sub-batch
            self.prev_count = 0 
            
            self.total_batches_created += 1
            new_name = f"SUB-BATCH {self.total_batches_created}"
            new_widget = SubBatchItem(
                batch_name=new_name,
                is_active=True
            )
            self.sub_batch_scrollview.add_widget(new_widget)
            self.sub_batch_history[new_name] = -1 
            self.current_active_widget = new_widget

    def remove_sub_batch(self, widget_to_remove, show_dialog=True, *args):
        # Reset the system state if we are deleting the active widget
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

        if show_dialog:
            # Show a confirmation dialog
            dialog = SystemDialog(
                dialog_title = "Remove Sub-batch",
                dialog_msg = "Are you sure you want to remove this Sub-batch? This process cannot be undone.", 
                mode = "destructive", 
                command_on_proceed = execute_deletion)
            dialog.open()
        else:
            execute_deletion()

    #[SECTION] Database Functions
    #dev: checked, it: 01
    def save_batch_log(self):
        """Calculates or assigns the final values for keys in the payload."""
        self.payload.update({
            "local_id": self.batch_uuid,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f+00"), # Format to ISO-8601 / PostgreSQL timestamptz
            "batch_id": self.name_count_batch,
            "op_name": self.name_operator,
            "count_total_pl": self.total_count,
            "num_sbatch": len(self.sub_batch_history),
            "count_per_sbatch": self.sub_batch_history,
            "model_version": self.model_path,
            "rel": sum(self.reliability_scores)/max(len(self.reliability_scores),1),
            "ave_temp": sum(self.water_temp_array)/max(len(self.water_temp_array),1),
            "ave_approx_density": self.total_count/max((sum(self.water_vol_array)/max(len(self.water_temp_array),1)),1),
            "time_elapsed": sum(self.count_timer_array)
        })
        cached_payload = copy.deepcopy(self.payload)

        #dev: checked, it: 01
        def push_data():
            try:
                self.db_client.table("system_logs").insert(cached_payload).execute()
                print("[INFO] Log Saved to Database:")

                for key, value in cached_payload.items():
                    print(f"{key}: {value} | type: {type(value)}")

                Clock.schedule_once(lambda dt: self.show_snackbar(warning_mode = False, message=f"{cached_payload['batch_id']} is saved to Logs"))

            except Exception as e:
                err = e
                print(f"[DEBUG] Failed to Push Batch Count Log on Database: {err}")
                save_to_local()
                Clock.schedule_once(lambda dt: self.show_snackbar(warning_mode=True, message=f"Failed to push log on cloud, log is saved locally"))

        #dev: checked, it: 01
        def save_to_local():
            try:
                folder_name = "pending_sync"
                os.makedirs(folder_name, exist_ok=True) 

                filename = f"{cached_payload['local_id']}.json"
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

    #dev: checked, it: 01
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
            response = self.db_client.table("system_logs").select("*").order("timestamp", desc=True).limit(1000).execute()
            
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
                                self.db_client.table("system_logs").insert(log_data).execute()
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
                key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S.%f+00"), 
                reverse=True
            )
        except Exception as e:
            print(f"[DEBUG] Sorting error (likely a timestamp format mismatch): {e}")

        #FORMAT FOR RECYCLEVIEW & UPDATE UI
        rv_data = []
        for log in master_log_list:
            rv_data.append({
                "log_uuid": str(log.get("local_id", "NULL")),
                "log_id_batch": str(log.get("batch_id", "UNKNOWN")),
                "log_timestamp": str(log.get("timestamp", "No Date")),
                "log_name_op": str(log.get("op_name", "Unknown Operator")),
                "log_pl_count": int(log.get("count_total_pl", 0)),
                "log_num_sbatches": int(log.get("num_sbatch", 0)),
                "log_margin_of_err": float(log.get("rel", 0.0)),
                "log_loc": str(log.get("log_loc", "UNKNOWN")),
                "log_time_elapsed": float(log.get("time_elapsed", 0.0))
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
                self.db_client.table("system_logs").delete().eq("local_id", target_uuid).execute()
                rv.data = [item for item in rv.data if item.get('local_id') != target_uuid]
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
                    rv.data = [item for item in rv.data if item.get('local_id') != target_uuid]
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

    def config_scrn_brightness(self, instance, slider_value):
        """Adjust screen brightness via Kivy Slider. Set minimum to 10 and maximum to 255"""
        brightness_level = int(slider_value)
        
        try:
            backlight_paths = glob.glob('/sys/class/backlight/*/brightness')
            
            if backlight_paths:
                with open(backlight_paths[0], 'w') as f:
                    f.write(str(brightness_level))
                    
        except PermissionError:
            print("[ERROR] Kivy does not have Linux permission to modify hardware.")

    def export_logs(self, email:str, timerange:str, *args):
        self.show_snackbar(message="Preparing export... Please wait.")
        if timerange == "all_time":
            all_time = True
        elif timerange == "last_7":
            days_window = 7
        elif timerange == "last_30":
            days_window = 30
        else:
            print("[ERROR] Invalid given timeframe.")
            Clock.schedule_once(lambda dt: self.show_snackbar(warning_mode=True, message="Failed to export. Invalid timeframe."))
            pass
        
        def fetch_logs():
            """Fetches batch logs within the given specific time window."""
            try:
                if all_time:
                    response = self.db_client.table("system_logs") \
                        .select("*").execute()
                else:
                    time_format = "%Y-%m-%d %H:%M:%S.%f+00"
                    end_time = time.now()
                    start_time = end_time - timedelta(days_window)
                    print(f"[INFO] Fetching Logs from {end_time.strf(time_format)}")
                    response = self.db_client.table("system_logs") \
                        .select("*") \
                        .gte("timestamp", start_time.strf(time_format)) \
                        .lte("timestamp", end_time.strf(time_format)) \
                        .execute()

                fetched_data = response.data
                print(f"[INFO] Fetched {len(fetched_data)} logs from Supabase.")
                return fetched_data

            except Exception as e:
                print(f"[ERROR] Failed to fetch data: {e}")
                return []
            
        def _export_worker():
            try:
                raw_data = fetch_logs()
                if not raw_data:
                    Clock.schedule_once(lambda dt: self.show_snackbar(warning_mode=True, message="No logs found for this timeframe."))
                    return

                csv_filename = f"log_export_{timerange}.csv"
                with open(csv_filename, mode='w', newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=raw_data[0].keys())
                    writer.writeheader()
                    writer.writerows(raw_data)

                sender_email = "noreply.ulang.pl.counter.system@gmail.com"
                app_password = "jqrstqxgasqkvmaz"

                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = email
                msg['Subject'] = f"Ulang Hatchery - Batch Logs ({timerange})"
                msg.attach(MIMEText(f"Attached is the requested CSV log export for: {timerange}.", 'plain'))

                with open(csv_filename, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={csv_filename}")
                msg.attach(part)

                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender_email, app_password)
                server.send_message(msg)
                server.quit()

                if os.path.exists(csv_filename):
                    os.remove(csv_filename)

                Clock.schedule_once(lambda dt: self.show_snackbar(message=f"Logs sent successfully to {email}!"))

            except Exception as e:
                print(f"[ERROR] Export Failed: {e}")
                Clock.schedule_once(lambda dt: self.show_snackbar(warning_mode=True, message="Failed to send email"))

        threading.Thread(target=_export_worker, daemon=True).start()

    def config_cam_res(self, opt):
        self.def_cam_res = opt

    def check_chamber_stat(self, dt):
        self.monitoring_freezed = False

        if dt: print(f"[INFO] Chamber is checked after {dt} seconds.")

        if ((self.water_temp > self.max_temp) or (self.water_temp < self.min_temp)):
            self.active_alert = True
            self.critical_temp = True
            self.stop_camera()
            print("[WARNING] Critical Water Temperature")

        else:
            self.active_alert = False
            self.critical_temp = False

        if self.water_vol > self.max_load:
            self.critical_load = True
            self.active_alert = True
            self.stop_camera()
            print("[WARNING] Critical Water Level")

        else:
            if not self.critical_temp: self.active_alert = False
            self.critical_load = False

        if self.active_alert:
            self.start_camera_loading(anti_loop=True) # Start loading camera to check for stats

    def finish_queue_check_stat(self):
        Clock.schedule_once(self.check_chamber_stat, timeout = 5)

    def freeze_alert(self):
        """Temporarily freeze check_chamber_stat()"""
        self.monitoring_freezed = True
        self.finish_queue_check_stat()
        self.start_camera_loading() # Start loading camera again
#=====================================================Graphics====================================================

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
            if self.is_active:
                if self.cmd_on and callable(self.cmd_on): 
                    self.cmd_on()

            else:
                if self.cmd_off and callable(self.cmd_off): 
                    self.cmd_off()
                
        else:
            print(f"[{self.text}] Standard Push Triggered!")

    def on_is_active(self, instance, value):
        if value:
            self.current_color = self.color_on
        else:
            self.current_color = self.color_off

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
        anim = Animation(knob_pos=target_x, duration=0.2, t=smooth_anim_curve)
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

class ToggleSwitch(ButtonBehavior, Widget):
    active = BooleanProperty(False)
    knob_pos = NumericProperty(dp(2)) 

    def on_release(self):
            self.active = not self.active
    
    def on_active(self, instance, value):
        if value:
            target_x = self.width - self.height + dp(2)
        else:
            target_x = dp(2)
        anim = Animation(knob_pos=target_x, duration=0.35, t=smooth_anim_curve)
        anim.start(self)

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

class ExportLogsDialog(Popup):
    input_timerange = OptionProperty("all_time", options=["last_7", "last_30", "all_time"])
    command_on_proceed = ObjectProperty(None, allownone=True)
    palette = ObjectProperty(None, allownone=True)

    def on_pre_open(self):
        self.set_timerange("all_time")

    def set_timerange(self, id):
        if id == 'opt_1':
            self.input_timerange = "last_7"
            self.ids.opt_1.md_bg_color = get_color_from_hex(self.palette["blue"])
            self.ids.opt_2.md_bg_color = get_color_from_hex(self.palette["dark_gray"])
            self.ids.opt_3.md_bg_color = get_color_from_hex(self.palette["dark_gray"])
        elif id == 'opt_2':
            self.input_timerange = "last_30"
            self.ids.opt_1.md_bg_color = get_color_from_hex(self.palette["dark_gray"])
            self.ids.opt_2.md_bg_color = get_color_from_hex(self.palette["blue"])
            self.ids.opt_3.md_bg_color = get_color_from_hex(self.palette["dark_gray"])
        else:
            self.input_timerange = "all_time"
            self.ids.opt_1.md_bg_color = get_color_from_hex(self.palette["dark_gray"])
            self.ids.opt_2.md_bg_color = get_color_from_hex(self.palette["dark_gray"])
            self.ids.opt_3.md_bg_color = get_color_from_hex(self.palette["blue"])

    def execute_proceed(self, email, timerange):
        if self.command_on_proceed and callable(self.command_on_proceed): 
            self.command_on_proceed(email, timerange)
        self.dismiss()

class CamResDialog(Popup):
    default_opt = ObjectProperty(None, allownone=True)
    selected_opt = OptionProperty(default_opt, options=["4K", "2K", "1080p"])
    command_on_proceed = ObjectProperty(None, allownone=True)
    palette = ObjectProperty(None, allownone=True)

    def on_pre_open(self):
        if self.default_opt == "4K":
            opt = "opt_1"
        elif self.default_opt == "2K":
            opt = "opt_2"
        else:
            opt = "opt_3"

        self.select(opt)

    def select(self, id):
        if id == 'opt_1':
            self.selected_opt = "4K"
            self.ids.opt_1.md_bg_color = get_color_from_hex(self.palette["blue"])
            self.ids.opt_2.md_bg_color = get_color_from_hex(self.palette["dark_gray"])
            self.ids.opt_3.md_bg_color = get_color_from_hex(self.palette["dark_gray"])

        elif id == 'opt_2':
            self.selected_opt = "2K"
            self.ids.opt_1.md_bg_color = get_color_from_hex(self.palette["dark_gray"])
            self.ids.opt_2.md_bg_color = get_color_from_hex(self.palette["blue"])
            self.ids.opt_3.md_bg_color = get_color_from_hex(self.palette["dark_gray"])

        else:
            self.selected_opt = "1080p"
            self.ids.opt_1.md_bg_color = get_color_from_hex(self.palette["dark_gray"])
            self.ids.opt_2.md_bg_color = get_color_from_hex(self.palette["dark_gray"])
            self.ids.opt_3.md_bg_color = get_color_from_hex(self.palette["blue"])

    def execute_proceed(self, selected_opt):
        if self.command_on_proceed and callable(self.command_on_proceed): 
            self.command_on_proceed(selected_opt)
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
    log_time_elapsed = NumericProperty(0.0)

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

class SysIconButton(ButtonBehavior, BoxLayout):
    text = StringProperty("")
    icon = StringProperty("")
    background_normal = StringProperty("")
    background_down = StringProperty("")

class ClickableImage(ButtonBehavior, Image):
    pass
    
if __name__ == '__main__':
    UlangSystemApp().run()