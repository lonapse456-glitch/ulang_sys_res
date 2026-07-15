from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ObjectProperty
import random

KV = '''
# 1. THE CUSTOM SUB-BATCH WIDGET
<SubBatchItem>:
    orientation: "horizontal"
    size_hint_y: None
    height: "48dp"
    
    # Dynamic Highlight: If is_active is True, it turns Teal. If False, Dark Grey.
    md_bg_color: (0.1, 0.6, 0.6, 0.4) if root.is_active else (0.15, 0.15, 0.15, 1)

    MDLabel:
        text: root.batch_name
        font_name: "Roboto-Bold" # Swap to your sf_txt font later
        theme_text_color: "Custom"
        text_color: 1, 1, 1, 1
        halign: "left"
        
    MDLabel:
        # Show "Waiting..." until a count is actually provided
        text: str(root.count) if root.count >= 0 else "Waiting for AI..."
        theme_text_color: "Custom"
        text_color: (0.8, 0.8, 0.8, 1) if root.count < 0 else (1, 1, 1, 1)
        halign: "right"

# 2. THE DASHBOARD LAYOUT
MDBoxLayout:
    md_bg_color: 0.1, 0.1, 0.1, 1

    # LEFT PANE (Camera Placeholder)
    MDBoxLayout:
        size_hint_x: 0.6
        orientation: "vertical"
        padding: "24dp"
        
        MDLabel:
            text: "TOTAL PL COUNT"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 0.6, 0.6, 0.6, 1
            
        MDLabel:
            # Data Binding: This automatically updates when app.total_count changes!
            text: str(app.total_count)
            halign: "center"
            font_style: "H2"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1

    # RIGHT PANE (Dynamic ScrollView)
    MDBoxLayout:
        size_hint_x: 0.4
        orientation: "vertical"
        padding: "16dp"
        spacing: "16dp"

        # The Scrollable Area
        ScrollView:
            do_scroll_x: False
            
            MDBoxLayout:
                id: scroll_container
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height  # CRITICAL for scrolling
                spacing: "8dp"

        # The Action Button (Changes dynamically based on app.is_counting)
        Button:
            text: "START INFERENCE" if app.is_counting else "ADD SUB-BATCH"
            size_hint_y: None
            height: "56dp"
            font_size: "18sp"
            background_normal: ''
            # Turns Blue when adding, Green when counting
            background_color: (0.2, 0.6, 0.2, 1) if app.is_counting else (0.2, 0.4, 0.8, 1)
            on_release: app.handle_button_click()
'''

class SubBatchItem(MDBoxLayout):
    # These properties allow KV and Python to communicate instantly
    batch_name = StringProperty("")
    count = NumericProperty(-1) # -1 acts as our "empty" state
    is_active = BooleanProperty(False)

class UlangApp(MDApp):
    # Global System State
    total_count = NumericProperty(0)
    is_counting = BooleanProperty(False)
    
    # Data Storage
    sub_batch_history = [] 
    
    # We use this to remember which widget is currently highlighted
    current_active_widget = ObjectProperty(None, allownone=True)

    def build(self):
        return Builder.load_string(KV)

    def handle_button_click(self):
        if not self.is_counting:
            # === STATE 1: ADDING A SUB-BATCH ===
            self.is_counting = True
            
            # Figure out what number this batch is
            next_batch_num = len(self.sub_batch_history) + 1
            
            # Instantiate the custom visual widget
            new_widget = SubBatchItem(
                batch_name=f"Sub-Batch #{next_batch_num}",
                is_active=True # Highlight it immediately!
            )
            
            # Inject it into the ScrollView
            self.root.ids.scroll_container.add_widget(new_widget)
            
            # Save a reference to it so we can inject the count into it later
            self.current_active_widget = new_widget
            
        else:
            # === STATE 2: EXECUTING THE COUNT ===
            self.is_counting = False
            
            # 1. Simulate YOLOv8 inference 
            simulated_count = random.randint(40, 300)
            
            # 2. Update the Visual UI
            self.current_active_widget.count = simulated_count
            self.current_active_widget.is_active = False # Remove highlight
            
            # 3. Update the Backend Data
            self.total_count += simulated_count
            self.sub_batch_history.append(simulated_count)

            print(self.sub_batch_history)
            
            # Clear the reference for safety
            self.current_active_widget = None

if __name__ == '__main__':
    UlangApp().run()