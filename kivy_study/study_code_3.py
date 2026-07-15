import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

#Creating Buttons and Events

class MyGrid(GridLayout):
    def __init__(self, **kwargs):
        super(MyGrid, self).__init__(**kwargs)

        self.cols = 1

        self.inside = GridLayout()
        self.inside.cols = 2

        self.inside.add_widget(Label(text="First Name: "))
        self.firstname = TextInput(multiline = False)
        self.inside.add_widget(self.firstname)

        self.inside.add_widget(Label(text="Last Name: "))
        self.lastname = TextInput(multiline = False)
        self.inside.add_widget(self.lastname)

        self.inside.add_widget(Label(text="Middle Name: "))
        self.middlename = TextInput(multiline = False)
        self.inside.add_widget(self.middlename)

        self.add_widget(self.inside)

        self.submit = Button(text="Submit", font_size=40)
        self.submit.bind(on_press=self.pressed)
        self.add_widget(self.submit)

    def pressed(self, instance):
        first = self.firstname.text
        last = self.lastname.text
        middle = self.middlename.text

        print(f"Your full name is {first} {middle} {last}.")
        self.firstname.text = ""
        self.lastname.text = ""
        self.middlename.text = "W"

class MyApp(App):
    def build(self):
        return MyGrid()
    
if __name__ == "__main__":
    MyApp().run()