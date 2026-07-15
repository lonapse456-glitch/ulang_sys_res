from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.modalview import ModalView
from kivy.properties import StringProperty
from kivy.metrics import dp

# Lock the window to your 7-inch Raspberry Pi resolution
Window.size = (800, 480)

KV = '''
# ==========================================
# 1. CUSTOM SNACKBAR DESIGN
# ==========================================
<CustomImageSnackbar>:
    size_hint_y: None
    height: dp(60)
    
    # This is where your custom background goes!
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [15]
            # source: 'assets/your_snackbar_bg.png'  <-- UNCOMMENT AND USE YOUR IMAGE

    MDBoxLayout:
        padding: dp(15)
        spacing: dp(15)
        
        MDIcon:
            icon: "check-circle"
            theme_text_color: "Custom"
            text_color: 0.2, 0.8, 0.2, 1
            pos_hint: {"center_y": .5}
            
        MDLabel:
            text: root.text
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            shorten: True
            pos_hint: {"center_y": .5}

# ==========================================
# 2. CUSTOM DIALOG DESIGN (Using ModalView)
# ==========================================
<CustomImageDialog>:
    size_hint: 0.7, 0.6  # Takes up 70% width, 60% height
    background_color: 0, 0, 0, 0  # Makes the default modal box invisible
    background: ""                # Clears default graphics
    
    # Inject your custom image as the background
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [20]
            # source: 'assets/your_dialog_bg.png'  <-- UNCOMMENT AND USE YOUR IMAGE
            
    # The content inside your custom dialog
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(24)
        spacing: dp(10)
        
        MDLabel:
            text: "SYSTEM WARNING"
            font_style: "H5"
            bold: True
            theme_text_color: "Custom"
            text_color: 0.9, 0.2, 0.2, 1  # Red text
            size_hint_y: 0.2
            
        MDLabel:
            text: "Are you sure you want to clear the entire batch database? This cannot be undone."
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            size_hint_y: 0.6
            
        MDBoxLayout:
            size_hint_y: 0.2
            spacing: dp(15)
            
            MDFillRoundFlatButton:
                text: "CANCEL"
                size_hint_x: 0.5
                md_bg_color: 0.3, 0.3, 0.3, 1
                on_release: root.dismiss()  # Closes the dialog
                
            MDFillRoundFlatButton:
                text: "DELETE LOGS"
                size_hint_x: 0.5
                md_bg_color: 0.8, 0.2, 0.2, 1
                on_release: 
                    root.dismiss()

# ==========================================
# MAIN SCREEN
# ==========================================
MDScreen:
    md_bg_color: 0.08, 0.08, 0.08, 1

    MDBoxLayout:
        orientation: 'vertical'
        spacing: dp(20)
        pos_hint: {"center_x": .5, "center_y": .5}
        adaptive_height: True

        MDFillRoundFlatButton:
            text: "TEST CUSTOM DIALOG"
            pos_hint: {"center_x": .5}
            size_hint_x: 0.5
            on_release: app.trigger_custom_dialog()
'''

# 2. Python Class for Custom Dialog
class CustomImageDialog(ModalView):
    pass

class AlertDemoApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)

    def trigger_custom_dialog(self):
        """Creates and shows our custom-imaged ModalView dialog."""
        dialog = CustomImageDialog()
        dialog.open()

if __name__ == '__main__':
    AlertDemoApp().run()