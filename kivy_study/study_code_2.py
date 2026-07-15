import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput

#Labels, Input and GUI Layouts

class MyGrid(GridLayout):
    def __init__(self, **kwargs):
        super(MyGrid, self).__init__(**kwargs)
        self.cols = 2
        self.add_widget(Label(text="First Name: "))
        self.firstname = TextInput(multiline = False)
        self.add_widget(self.firstname)

        self.add_widget(Label(text="Last Name: "))
        self.lastname = TextInput(multiline = False)
        self.add_widget(self.lastname)

        self.add_widget(Label(text="Middle Name: "))
        self.middlename = TextInput(multiline = False)
        self.add_widget(self.middlename)

class MyApp(App):
    def build(self):
        return MyGrid()
    
if __name__ == "__main__":
    MyApp().run()