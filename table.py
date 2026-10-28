"""Play surface and management of cards currently on the table."""

from pathlib import Path

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout

from card import CardOnTable


class TableSurface(FloatLayout):
    """Fixed table surface. Card Scatter widgets are independent children."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # The table colors and felt border are defined in table.kv.
        self.bind(pos=self._sync_table_layout, size=self._sync_table_layout)
        self.cards = {}
        self.discarded = {}

    def _sync_table_layout(self, *_):
        # Make cards as large as practical on the table while leaving a
        # little room around them; preserve the original 280:430 proportions.
        card_w = min(self.width * 0.90, self.height * 0.88 * 280 / 430)
        card_h = card_w * 430 / 280
        for card in self.cards.values():
            card.size = (card_w, card_h)

    def add_card(self, card_id, deck_path):
        if card_id in self.discarded:
            self.restore_card(card_id)
            return
        if card_id in self.cards:
            card = self.cards[card_id]
            card.center = self.center
            card.rotation = 0
            self.bring_to_front(card)
            return
        card = CardOnTable(card_id, deck_path, self.discard_card)
        # Use the same maximum-fit sizing as existing cards on the table.
        card_w = min(self.width * 0.90, self.height * 0.88 * 280 / 430)
        card_h = card_w * 430 / 280
        card.size = (card_w, card_h)
        card.center = (self.width / 2 + (len(self.cards) % 5) * dp(22),
                       self.height / 2 + (len(self.cards) % 4) * dp(18))
        self.cards[card_id] = card
        self.add_widget(card)

    def bring_to_front(self, card):
        if card.parent is self:
            self.remove_widget(card)
            self.add_widget(card)

    def discard_card(self, card):
        self.cards.pop(card.card_id, None)
        if card.parent is self:
            self.remove_widget(card)
        self.discarded[card.card_id] = card

    def restore_card(self, card_id):
        card = self.discarded.pop(card_id, None)
        if card is None:
            return
        self.cards[card_id] = card
        card.center = self.center
        self.add_widget(card)


# Load the appearance rules after defining TableSurface.
Builder.load_file(str(Path(__file__).resolve().parent / "table.kv"))
