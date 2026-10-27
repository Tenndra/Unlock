from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatter import Scatter
from card_layout import CardLayout


MAX_CARD_NUMBER = 10
ROWS_NUMBER = MAX_CARD_NUMBER // 5
COLS_NUMBER = MAX_CARD_NUMBER // ROWS_NUMBER

SPACING_X = 0.1
SPACING_Y = 0.1


class GameboardLayout(BoxLayout):
    card_layout_list = []
    free_position_list = list(range(10))

    def __init__(self, deck, **kwargs):
        super().__init__(**kwargs)
        self.deck = deck
        self.pic_a_card('start')
        self.size_hint = (1, 1)

    """def pic_a_card(self, card_number):
        index = self.free_position_list[0]
        self.free_position_list.remove(index)

        x = index % COLS_NUMBER * (1 / COLS_NUMBER)
        y = index // COLS_NUMBER * (1 / ROWS_NUMBER)

        card_layout = CardLayout(card_number, self.deck, self.delete_card, pos_hint={'x': x, 'y': y})
        self.card_layout_list.append(card_layout)
        self.add_widget(card_layout)"""

    def pic_a_card(self, card_number):
        if not self.free_position_list:
            return

        index = self.free_position_list.pop(0)

        card_width = self.width / COLS_NUMBER
        card_height = self.height / ROWS_NUMBER

        x = (index % COLS_NUMBER) * card_width
        y = (index // COLS_NUMBER) * card_height

        card_layout = CardLayout(
            card_number,
            self.deck,
            self.delete_card,
            size=(card_width, card_height),
            pos=(x, y),
            size_hint=(None, None),
        )

        self.card_layout_list.append(card_layout)
        self.add_widget(card_layout)

    def delete_card(self, card_layout):
        index = self.card_layout_list.index(card_layout)

        self.remove_widget(card_layout)
        self.card_layout_list.remove(card_layout)

        self.free_position_list.append(index)
        self.free_position_list.sort()
