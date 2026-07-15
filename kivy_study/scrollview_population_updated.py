from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ObjectProperty
import random

KV = '''
# 1. THE UPDATED SUB-BATCH WIDGET (Now with a Delete Button)
<SubBatchItem>:
    orientation: "horizontal"
    size_hint_y: None
    height: "48dp"
    
    md_bg_color: (0.1, 0.6, 0.6, 0.4) if root.is_active else (0.15, 0.15, 0.15, 1)

    MDLabel:
        text: root.batch_name
        font_name: "Roboto-Bold"
        theme_text_color: "Custom"
        text_color: 1, 1, 1, 1
        halign: "left"
        
    MDLabel:
        text: str(root.count) if root.count >= 0 else "Waiting..."
        theme_text_color: "Custom"
        text_color: (0.8, 0.8, 0.8, 1) if root.count < 0 else (1, 1, 1, 1)
        halign: "right"

    # THE NEW TRASH BUTTON
    MDIconButton:
        icon: "trash-can-outline"
        theme_text_color: "Custom"
        text_color: 0.8, 0.2, 0.2, 1 # Red icon
        # Pass THIS specific widget (root) back to the main app to be deleted
        on_release: app.remove_sub_batch(root)

# 2. THE DASHBOARD LAYOUT (Remains mostly the same)
MDBoxLayout:
    md_bg_color: 0.1, 0.1, 0.1, 1

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
            text: str(app.total_count)
            halign: "center"
            font_style: "H2"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1

    MDBoxLayout:
        size_hint_x: 0.4
        orientation: "vertical"
        padding: "16dp"
        spacing: "16dp"

        ScrollView:
            do_scroll_x: False
            
            MDBoxLayout:
                id: scroll_container
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: "8dp"

        Button:
            text: "START INFERENCE" if app.is_counting else "ADD SUB-BATCH"
            size_hint_y: None
            height: "56dp"
            font_size: "18sp"
            background_normal: ''
            background_color: (0.2, 0.6, 0.2, 1) if app.is_counting else (0.2, 0.4, 0.8, 1)
            on_release: app.handle_button_click()
'''

class SubBatchItem(MDBoxLayout):
    batch_name = StringProperty("")
    count = NumericProperty(-1)
    is_active = BooleanProperty(False)

class UlangApp(MDApp):
    total_count = NumericProperty(0)
    is_counting = BooleanProperty(False)
    
    # NEW: Absolute counter to ensure unique IDs
    total_batches_created = NumericProperty(0) 
    
    # NEW: Upgraded backend to a dictionary to track specific batch names
    sub_batch_history = {} 
    
    current_active_widget = ObjectProperty(None, allownone=True)

    def build(self):
        return Builder.load_string(KV)

    def handle_button_click(self):
        if not self.is_counting:
            # === STATE 1: ADDING A SUB-BATCH ===
            self.is_counting = True
            
            # Increment the absolute counter
            self.total_batches_created += 1
            new_name = f"Sub-Batch #{self.total_batches_created}"
            
            new_widget = SubBatchItem(
                batch_name=new_name,
                is_active=True
            )
            
            # Add to UI and Backend Data
            self.root.ids.scroll_container.add_widget(new_widget)
            self.sub_batch_history[new_name] = -1 
            self.current_active_widget = new_widget
            
        else:
            # === STATE 2: EXECUTING THE COUNT ===
            self.is_counting = False
            simulated_count = random.randint(40, 300)
            
            # Update UI Widget
            self.current_active_widget.count = simulated_count
            self.current_active_widget.is_active = False
            
            # Update Backend Data
            self.total_count += simulated_count
            self.sub_batch_history[self.current_active_widget.batch_name] = simulated_count
            
            self.current_active_widget = None

    # === NEW: THE DELETION LOGIC ===
    def remove_sub_batch(self, widget_to_remove):
        # 1. If we are deleting the active widget, reset the system state
        if widget_to_remove.is_active:
            self.is_counting = False
            self.current_active_widget = None
            
        # 2. Deduct from the Master Total (only if it actually had a count)
        if widget_to_remove.count > 0:
            self.total_count -= widget_to_remove.count
            
        # 3. Delete from the Backend Dictionary
        if widget_to_remove.batch_name in self.sub_batch_history:
            del self.sub_batch_history[widget_to_remove.batch_name]
            
        # 4. Destroy the visual widget from the ScrollView
        self.root.ids.scroll_container.remove_widget(widget_to_remove)
        
        print(f"Removed {widget_to_remove.batch_name}. Current Backend Data:", self.sub_batch_history)

if __name__ == '__main__':
    UlangApp().run()