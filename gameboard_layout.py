from kivy.uix.relativelayout import RelativeLayout

from card_layout import CardLayout

MAX_CARD_NUMBER = 10
ROWS_NUMBER = MAX_CARD_NUMBER // 5
COLS_NUMBER = MAX_CARD_NUMBER // ROWS_NUMBER

SPACING_X = 0.1
SPACING_Y = 0.1


class GameboardLayout(RelativeLayout):
    card_layout_list = []
    free_position_list = list(range(10))

    def __init__(self, deck, **kwargs):
        super().__init__(**kwargs)
        self.deck = deck
        self.pic_a_card('start')

    def pic_a_card(self, card_number):
        index = self.free_position_list[0]
        self.free_position_list.remove(index)

        card_layout_width = self.width // COLS_NUMBER
        card_layout_height = self.height // ROWS_NUMBER

        """x = (index % COLS_NUMBER) * card_layout_width
        y = (index // COLS_NUMBER) * card_layout_height"""

        x = index % COLS_NUMBER * (1 / COLS_NUMBER)
        y = index // COLS_NUMBER * (1 / ROWS_NUMBER)

        # Je pense que je dois utiliser des pos_hint p

        card_layout = CardLayout(card_number, self.deck, self.delete_card, pos_hint={'x': x, 'y': y})
        self.card_layout_list.append(card_layout)
        self.add_widget(card_layout)

    def delete_card(self, card_layout):
        index = self.card_layout_list.index(card_layout)

        self.remove_widget(card_layout)
        self.card_layout_list.remove(card_layout)

        self.free_position_list.append(index)
        self.free_position_list.sort()
