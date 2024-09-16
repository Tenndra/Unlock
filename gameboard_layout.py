from kivy.uix.relativelayout import RelativeLayout

from card_layout import CardLayout

MAX_CARD_NUMBER = 10


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

        x = (index % 5) * self.width * 0.2
        y = (index // 5) * self.height * 0.5

        card_layout = CardLayout(card_number, self.deck, self.delete_card, pos=(x, y))
        self.card_layout_list.append(card_layout)
        self.add_widget(card_layout)

    def delete_card(self, card_layout):
        index = self.card_layout_list.index(card_layout)

        self.remove_widget(card_layout)
        self.card_layout_list.remove(card_layout)

        self.free_position_list.append(index)
        self.free_position_list.sort()


