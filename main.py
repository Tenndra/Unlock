from kivy.config import Config
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatterlayout import ScatterLayout

WIDTH = 1920
HEIGHT = 1080
SIDE_BUTTON_WIDTH = 0.025

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

DECK = "La cabane de la sorciere"


class MainWidget(BoxLayout):
    deck = DECK
    card_list = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.width = WIDTH
        self.height = HEIGHT
        self.get_card_list()

        button_layout = ButtonLayout(self.card_list, self.pic_a_card, size_hint_x = SIDE_BUTTON_WIDTH)
        self.add_widget(button_layout)

        self.gameboard_layout = GameboardLayout(DECK, width=WIDTH-SIDE_BUTTON_WIDTH, height=HEIGHT)
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
