from kivy.properties import StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown


class MethodSelect(BoxLayout):
    descr = StringProperty()

    def __init__(self, **kwargs):
        self.descr = kwargs.pop('descr')
        self.options = kwargs.pop('methods')
        self.on_select = kwargs.pop('on_select')
        super().__init__(**kwargs)

        dropdown = DropDown()
        for option in self.options:
            btn = Button(text=option, size_hint=(None, None), height="30dp", background_color=(1,1,1,1))
            btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(btn)

        anch = AnchorLayout()
        drop_button = Button(text=self.options[0], size_hint=(None, 1), pos_hint={"center": 1})
        drop_button.bind(on_press=lambda btn: dropdown.open(btn))

        def on_select_option(instance, choice):
            """Called by the drop_button on option select"""
            setattr(drop_button, 'text', choice)
            self.on_select(choice)

        dropdown.bind(on_select=on_select_option)
        anch.add_widget(drop_button)
        self.add_widget(anch)
