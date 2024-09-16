from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

SIDE_BUTTON_WIDTH = 0.07


class ButtonLayout(BoxLayout):
    def __init__(self, card_list, callback, **kwargs):
        super().__init__(**kwargs)
        for card_name in card_list:
            button = PicButton(card_name, callback)
            self.add_widget(button)
            self.size_hint_x = SIDE_BUTTON_WIDTH


class PicButton(Button):

    def __init__(self, card_name, callback, **kwargs):
        super().__init__(**kwargs)
        self.card_name = card_name
        self.callback = callback
        self.text = card_name

    def on_press(self):
        self.callback(self.card_name)
        self.disabled = True
