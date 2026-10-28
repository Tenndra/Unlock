"""Play surface and management of cards currently on the table."""

from pathlib import Path

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label

from card import CardOnTable


class DiscardPile(BoxLayout):
    """Fixed drop target showing a thumbnail of the most recently discarded card."""

    count = NumericProperty(0)
    image_source = StringProperty("")

    def __init__(self, on_open, **kwargs):
        super().__init__(**kwargs)
        self.on_open_callback = on_open
        self.orientation = "vertical"
        self.size_hint = (None, None)
        self.size = (dp(112), dp(126))
        self.padding = dp(6)
        self.spacing = dp(3)
        self.title = Label(
            text="DÉFAUSSE · 0",
            size_hint_y=None,
            height=dp(20),
            font_size=dp(10),
            bold=True,
        )
        self.thumbnail = Image(
            source="",
            fit_mode="contain",
            size_hint=(1, 1),
        )
        self.hint = Label(
            text="Glisser ici",
            size_hint_y=None,
            height=dp(16),
            font_size=dp(9),
        )
        self.add_widget(self.title)
        self.add_widget(self.thumbnail)
        self.add_widget(self.hint)
        self.bind(count=self._refresh, image_source=self._refresh)

    def _refresh(self, *_):
        self.title.text = f"DÉFAUSSE · {self.count}"
        self.thumbnail.source = self.image_source
        self.thumbnail.reload()
        self.hint.text = "Glisser ici" if self.count == 0 else "Déposer une carte"

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.on_open_callback()
            return True
        return super().on_touch_down(touch)


class TableSurface(FloatLayout):
    """Fixed table surface. Card Scatter widgets are independent children."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._sync_table_layout, size=self._sync_table_layout)
        self.cards = {}
        self.discarded = {}
        self.on_card_discarded = None
        self.discard_pile = DiscardPile(self._open_discard)
        self.add_widget(self.discard_pile)
        self._sync_table_layout()

    def _open_discard(self):
        if callable(self.on_open_discard):
            self.on_open_discard()

    def _sync_table_layout(self, *_):
        # The printed card has no extra button strip; preserve its 280:430 ratio.
        available_h = max(0, self.height * 0.88)
        card_w = min(self.width * 0.90, available_h * 280 / 430)
        card_h = card_w * 430 / 280
        for card in self.cards.values():
            card.size = (card_w, card_h)
        if hasattr(self, "discard_pile"):
            self.discard_pile.pos = (
                self.x + self.width - self.discard_pile.width - dp(20),
                self.y + dp(18),
            )
            # Keep the target visible above cards, while it remains a passive
            # drop target during a drag that began on a card.
            self.bring_to_front(self.discard_pile)

    def add_card(self, card_id, deck_path):
        if card_id in self.discarded:
            self.restore_card(card_id)
            return
        if card_id in self.cards:
            card = self.cards[card_id]
            card.center = self.center
            card.rotation = 0
            self.bring_to_front(card)
            self.bring_to_front(self.discard_pile)
            return

        card = CardOnTable(card_id, deck_path, self.discard_card)
        available_h = max(0, self.height * 0.88)
        card_w = min(self.width * 0.90, available_h * 280 / 430)
        card_h = card_w * 430 / 280
        card.size = (card_w, card_h)
        card.center = (self.width / 2 + (len(self.cards) % 5) * dp(22),
                       self.height / 2 + (len(self.cards) % 4) * dp(18))
        self.cards[card_id] = card
        self.add_widget(card)
        self.bring_to_front(self.discard_pile)

    def bring_to_front(self, widget):
        if widget.parent is self:
            self.remove_widget(widget)
            self.add_widget(widget)

    def discard_card(self, card):
        self.cards.pop(card.card_id, None)
        if card.parent is self:
            self.remove_widget(card)
        self.discarded[card.card_id] = card
        self.discard_pile.count = len(self.discarded)
        # The top of the pile previews the most recently discarded card.
        self.discard_pile.image_source = str(card.picture.source)
        self.bring_to_front(self.discard_pile)
        if callable(self.on_card_discarded):
            self.on_card_discarded(card.card_id)

    def restore_card(self, card_id):
        card = self.discarded.pop(card_id, None)
        if card is None:
            return
        self.cards[card_id] = card
        card.center = self.center
        self.add_widget(card)
        self.discard_pile.count = len(self.discarded)
        latest = next(reversed(self.discarded.values()), None) if self.discarded else None
        self.discard_pile.image_source = str(latest.picture.source) if latest else ""
        self.bring_to_front(self.discard_pile)


# Load the appearance rules after defining TableSurface.
Builder.load_file(str(Path(__file__).resolve().parent / "table.kv"))
