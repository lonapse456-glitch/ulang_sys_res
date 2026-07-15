from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton

# Lock the window to your 7-inch Raspberry Pi resolution for testing
Window.size = (800, 480)

KV = '''
MDScreen:
    md_bg_color: 0.1, 0.1, 0.1, 1

    MDBoxLayout:
        orientation: 'vertical'
        spacing: dp(20)
        padding: dp(50)
        pos_hint: {"center_x": .5, "center_y": .5}
        adaptive_height: True

        MDLabel:
            text: "Ulang System Alert Demo"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            font_style: "H5"

        MDFillRoundFlatButton:
            text: "1. Trigger Snackbar (Export USB)"
            pos_hint: {"center_x": .5}
            size_hint_x: 0.6
            md_bg_color: 0.1, 0.5, 0.2, 1
            on_release: app.show_snackbar()

        MDFillRoundFlatButton:
            text: "2. Trigger Dialog (Clear History)"
            pos_hint: {"center_x": .5}
            size_hint_x: 0.6
            md_bg_color: 0.8, 0.2, 0.2, 1
            on_release: app.show_dialog()
'''

class AlertDemoApp(MDApp):
    dialog = None  # We store the dialog instance here so we can close it later

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        return Builder.load_string(KV)

    # ==========================================
    # 1. THE SNACKBAR IMPLEMENTATION
    # ==========================================
    def show_snackbar(self):
        """A Snackbar pops up from the bottom and disappears automatically."""
        Snackbar(
            text="Successfully exported logs to USB drive.",
            snackbar_x="10dp",
            snackbar_y="10dp",
            size_hint_x=(Window.width - 20) / Window.width,
            bg_color=(0.2, 0.6, 0.2, 1), # Custom green background
            duration=2.5 # Disappears after 2.5 seconds
        ).open()

    # ==========================================
    # 2. THE DIALOG IMPLEMENTATION
    # ==========================================
    def show_dialog(self):
        """A Dialog dims the background and forces the user to make a choice."""
        if not self.dialog:
            self.dialog = MDDialog(
                title="Clear Batch History?",
                text="This action cannot be undone. All local logs will be permanently deleted from the system.",
                buttons=[
                    # Cancel Button
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=self.close_dialog
                    ),
                    # Destructive/Confirm Button
                    MDFlatButton(
                        text="DELETE",
                        theme_text_color="Custom",
                        text_color=(0.9, 0.2, 0.2, 1), # Red warning text
                        on_release=self.execute_delete
                    ),
                ],
            )
        self.dialog.open()

    def close_dialog(self, *args):
        """Simply closes the dialog window without doing anything."""
        self.dialog.dismiss()

    def execute_delete(self, *args):
        """Executes the action, closes the dialog, and confirms via snackbar."""
        print("Database cleared!")
        self.dialog.dismiss()
        Snackbar(text="Batch history has been completely wiped.").open()

if __name__ == '__main__':
    AlertDemoApp().run()