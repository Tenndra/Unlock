from kivy.config import Config

WIDTH = 1920
HEIGHT = 1080

Config.set('graphics', 'width', str(WIDTH))
Config.set('graphics', 'height', str(HEIGHT))

from kivy.core.window import Window
Window.fullscreen = True

import os

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

from button_layout import ButtonLayout
from gameboard_layout import GameboardLayout

Builder.load_file('gameboard_layout.kv')
Builder.load_file('button_layout.kv')
Builder.load_file('card_layout.kv')

DECK = "Tutoriel"


class MainWidget(BoxLayout):
    deck = DECK
    card_list = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.get_card_list()

        button_layout = ButtonLayout(self.card_list, self.pic_a_card)
        self.add_widget(button_layout)

        self.gameboard_layout = GameboardLayout(DECK)
        self.add_widget(self.gameboard_layout)

    def get_card_list(self):
        directory = "ressources/decks/" + self.deck
        self.card_list = []
        for file in os.listdir(directory):
            filename = os.fsdecode(file)
            index = filename.index('_')
            card_name = filename[:index]
            try:
                int(card_name)
                if card_name not in self.card_list:
                    self.card_list.append(card_name)
            except ValueError:
                pass

    def pic_a_card(self, card_number):
        self.gameboard_layout.pic_a_card(card_number)


class UnlockApp(App):
    pass


UnlockApp().run()
