import kivy
from kivy.app import App
from kivy.uix.label import Label

#This study code is for setting up kivy, just a basic instantation of a window with a single text

class MyApp(App):
    def build(self):
        return Label(text = "Hello World")
    
if __name__ == "__main__":
    MyApp().run()