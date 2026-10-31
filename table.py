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
    """Fixed pile preview; click it to inspect discarded cards."""

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
            text="Clic pour consulter",
            size_hint_y=None,
            height=dp(16),
            font_size=dp(9),
        )
        self.title.color = (0.94, 0.92, 0.85, 1)
        self.thumbnail.color = (1, 1, 1, 1)
        self.hint.color = (0.78, 0.61, 0.31, 1)
        self.add_widget(self.title)
        self.add_widget(self.thumbnail)
        self.add_widget(self.hint)
        self.bind(count=self._refresh, image_source=self._refresh)

    def _refresh(self, *_):
        self.title.text = f"DÉFAUSSE · {self.count}"
        self.thumbnail.source = self.image_source
        self.thumbnail.reload()
        self.hint.text = "Clic pour consulter"

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
        self.on_card_returned_to_deck = None
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
            self.bring_to_front(self.discard_pile)

    def _find_card_position(self, card_w, card_h):
        """Find a reasonably free position, allowing slight card overlap."""
        margin = dp(14)
        half_w, half_h = card_w / 2, card_h / 2
        min_x, max_x = self.x + margin + half_w, self.right - margin - half_w
        min_y, max_y = self.y + margin + half_h, self.top - margin - half_h

        if min_x > max_x or min_y > max_y:
            return self.center

        step_x = max(dp(28), card_w * 0.48)
        step_y = max(dp(28), card_h * 0.48)
        xs, ys = [], []
        value = min_x
        while value <= max_x:
            xs.append(value)
            value += step_x
        if not xs or xs[-1] < max_x - dp(2):
            xs.append(max_x)
        value = min_y
        while value <= max_y:
            ys.append(value)
            value += step_y
        if not ys or ys[-1] < max_y - dp(2):
            ys.append(max_y)

        existing = []
        for card in self.cards.values():
            existing.append((
                card.center_x - card.width / 2,
                card.center_y - card.height / 2,
                card.center_x + card.width / 2,
                card.center_y + card.height / 2,
            ))

        pile = self.discard_pile
        best_position, best_score = self.center, float("inf")
        for cy in ys:
            for cx in xs:
                left, bottom = cx - half_w, cy - half_h
                right, top = cx + half_w, cy + half_h
                score = 0.0
                for other_left, other_bottom, other_right, other_top in existing:
                    overlap_w = max(0, min(right, other_right) - max(left, other_left))
                    overlap_h = max(0, min(top, other_top) - max(bottom, other_bottom))
                    score += overlap_w * overlap_h
                pile_overlap_w = max(0, min(right, pile.right) - max(left, pile.x))
                pile_overlap_h = max(0, min(top, pile.top) - max(bottom, pile.y))
                score += pile_overlap_w * pile_overlap_h * 2.0
                # Prefer positions closer to the middle when several are equally free.
                score += ((cx - self.center_x) ** 2 + (cy - self.center_y) ** 2) * 0.015
                if score < best_score:
                    best_score = score
                    best_position = (cx, cy)
        return best_position

    def add_card(self, card_id, deck_path):
        if card_id in self.discarded:
            self.restore_card(card_id)
            return
        if card_id in self.cards:
            card = self.cards[card_id]
            card.center = self._find_card_position(card.width, card.height)
            card.rotation = 0
            self.bring_to_front(card)
            self.bring_to_front(self.discard_pile)
            return

        card = CardOnTable(card_id, deck_path, self.discard_card,
                           self.return_card_to_deck)
        # Start cards at roughly half the maximum table size so the draw
        # instruction card and the other cards remain visible.
        available_h = max(0, self.height * 0.88)
        max_card_w = min(self.width * 0.90, available_h * 280 / 430)
        card_w = max(dp(90), max_card_w * 0.50)
        card_h = card_w * 430 / 280
        card.size = (card_w, card_h)
        card.center = self._find_card_position(card_w, card_h)
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

    def return_card_to_deck(self, card):
        """Remove a mistakenly drawn card and make it available again."""
        self.cards.pop(card.card_id, None)
        if card.parent is self:
            self.remove_widget(card)
        if callable(self.on_card_returned_to_deck):
            self.on_card_returned_to_deck(card.card_id)

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
