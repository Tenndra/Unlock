from __future__ import annotations

import os
from pathlib import Path

from kivy.config import Config
Config.set("graphics", "fullscreen", "auto")
Config.set("graphics", "resizable", "1")
Config.set("input", "mouse", "mouse,multitouch_on_demand")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scatter import Scatter
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle


ROOT = Path(__file__).resolve().parent
DECKS_DIR = ROOT / "ressources" / "decks"
Window.clearcolor = (0.08, 0.10, 0.12, 1)


def readable_name(path: Path) -> str:
    return path.stem[:-2]


class CardOnTable(Scatter):
    """A single physical-style card: only this widget moves and rotates."""

    card_id = StringProperty("")
    face_up = BooleanProperty(True)

    def __init__(self, card_id, deck_path, on_discard, **kwargs):
        super().__init__(**kwargs)
        self.card_id = card_id
        self.deck_path = Path(deck_path)
        self.on_discard_callback = on_discard
        self.recto = self.deck_path / f"{card_id}_r.jpg"
        self.verso = self.deck_path / f"{card_id}_v.jpg"
        # Larger default card size; keep the original card aspect ratio.
        self.size = (dp(360), dp(553))
        self.size_hint = (None, None)
        self.do_translation = True
        self.do_rotation = True
        self.do_scale = False
        self.auto_bring_to_front = True
        self.rotation = 0

        # Scatter does not lay out its child automatically: keep the panel
        # synchronized with the Scatter size or the visible card stays small.
        panel = BoxLayout(orientation="vertical", spacing=dp(1), padding=dp(2),
                          size_hint=(None, None), size=self.size)
        self.bind(size=lambda widget, value: setattr(panel, "size", value))
        self.picture = Image(
            source=str(self.recto),
            fit_mode="contain",
            allow_stretch=True,
        )
        panel.add_widget(self.picture)

        controls = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(1))
        turn_button = Button(text="Face", font_size=dp(9), padding=(dp(1), 0))
        turn_button.bind(on_release=lambda *_: self.turn_card())
        left_button = Button(text="↶", size_hint_x=None, width=dp(24), font_size=dp(13))
        left_button.bind(on_release=lambda *_: self.rotate_card(-15))
        right_button = Button(text="↷", size_hint_x=None, width=dp(24), font_size=dp(13))
        right_button.bind(on_release=lambda *_: self.rotate_card(15))
        discard_button = Button(text="Jeter", font_size=dp(9), padding=(dp(1), 0))
        discard_button.bind(on_release=lambda *_: self.discard())
        controls.add_widget(left_button)
        controls.add_widget(turn_button)
        controls.add_widget(right_button)
        controls.add_widget(discard_button)
        panel.add_widget(controls)
        self.add_widget(panel)

    def turn_card(self):
        self.face_up = not self.face_up
        candidate = self.recto if self.face_up else self.verso
        if candidate.exists():
            self.picture.source = str(candidate)
            self.picture.reload()

    def rotate_card(self, angle):
        self.rotation = (self.rotation + angle) % 360

    def discard(self):
        self.on_discard_callback(self)


class TableSurface(FloatLayout):
    """Fixed table surface. Card Scatter widgets are independent children."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.12, 0.19, 0.17, 1)
            self._table_bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_table_bg, size=self._sync_table_bg)
        self.cards = {}
        self.discarded = {}

    def _sync_table_bg(self, *_):
        self._table_bg.pos = self.pos
        self._table_bg.size = self.size
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


class UnlockTableApp(App):
    title = "Unlock — table virtuelle"

    def build(self):
        self.deck_path = None
        self.card_ids = []
        self.card_buttons = {}
        root = BoxLayout(orientation="vertical", spacing=dp(1))
        root.add_widget(self.build_toolbar())

        body = BoxLayout(spacing=dp(1))
        # A narrower sidebar leaves more room for the play area.
        sidebar = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(180),
                            padding=dp(4), spacing=dp(3))
        sidebar.add_widget(Label(text="CARTES DU PAQUET", size_hint_y=None, height=dp(24),
                                 bold=True, font_size=dp(11)))
        self.card_scroll = ScrollView(do_scroll_x=False, do_scroll_y=True, bar_width=dp(3))
        self.card_list_box = BoxLayout(orientation="vertical", size_hint_y=None,
                                        spacing=dp(1), padding=(0, dp(1)))
        self.card_list_box.bind(minimum_height=self.card_list_box.setter("height"))
        self.card_scroll.add_widget(self.card_list_box)
        self.card_scroll.bind(size=lambda *_: self._resize_card_buttons())
        sidebar.add_widget(self.card_scroll)
        body.add_widget(sidebar)

        self.table = TableSurface()
        body.add_widget(self.table)
        root.add_widget(body)
        self.load_deck(self.deck_spinner.text if hasattr(self, "deck_spinner") else self.available_decks()[0])
        return root

    def build_toolbar(self):
        bar = BoxLayout(size_hint_y=None, height=dp(54), padding=(dp(8), dp(6)), spacing=dp(8))
        title = Label(text="UNLOCK  /  TABLE VIRTUELLE", bold=True, size_hint_x=None,
                      width=dp(260), font_size=dp(16), halign="left", valign="middle")
        title.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        bar.add_widget(title)
        decks = self.available_decks()
        self.deck_spinner = Spinner(text=decks[0] if decks else "Aucun paquet",
                                    values=decks, size_hint_x=None, width=dp(280))
        self.deck_spinner.bind(text=lambda _spinner, value: self.load_deck(value))
        bar.add_widget(self.deck_spinner)
        bar.add_widget(Widget())
        help_button = Button(text="Aide", size_hint_x=None, width=dp(85))
        help_button.bind(on_release=lambda *_: self.show_help())
        bar.add_widget(help_button)
        discard_button = Button(text="Défausse", size_hint_x=None, width=dp(110))
        discard_button.bind(on_release=lambda *_: self.show_discard())
        bar.add_widget(discard_button)
        return bar

    def available_decks(self):
        if not DECKS_DIR.exists():
            return []
        return sorted(p.name for p in DECKS_DIR.iterdir() if p.is_dir())

    def load_deck(self, deck_name):
        if not deck_name or deck_name == "Aucun paquet":
            return
        path = DECKS_DIR / deck_name
        if not path.is_dir():
            return
        # Switching packages starts a clean table so cards from different decks
        # are never mixed accidentally.
        if hasattr(self, "table"):
            self.table.clear_widgets()
            self.table.cards.clear()
            self.table.discarded.clear()
        self.deck_path = path
        # A card is identified by the common filename prefix of *_r.jpg / *_v.jpg.
        rectos = sorted(path.glob("*_r.jpg"), key=lambda p: p.name.lower())
        self.card_ids = [readable_name(p) for p in rectos]
        self.refresh_card_list()

    def refresh_card_list(self):
        if not hasattr(self, "card_list_box"):
            return
        self.card_list_box.clear_widgets()
        self.card_buttons.clear()
        count = len(self.card_ids)
        if count == 0:
            self.card_list_box.height = 0
            return
        # Fit every card button into the visible list area; each button is square.
        available_h = max(1, self.card_scroll.height - dp(2))
        button_size = max(1, (available_h - dp(count - 1)) / count)
        for card_id in self.card_ids:
            button = Button(text=card_id, size_hint=(None, None),
                            width=button_size, height=button_size,
                            font_size=max(dp(6), min(dp(10), button_size * 0.48)),
                            halign="center", valign="middle",
                            text_size=(button_size - dp(2), button_size - dp(2)),
                            padding=(0, 0))
            button.bind(on_release=lambda _button, value=card_id: self.add_card(value))
            self.card_list_box.add_widget(button)
            self.card_buttons[card_id] = button
            self.update_card_button(card_id)
        self.card_list_box.height = count * button_size + max(0, count - 1) * dp(1) + dp(2)

    def _resize_card_buttons(self):
        # Recalculate sizes after the window or available sidebar height changes.
        if hasattr(self, "card_list_box") and self.card_ids:
            self.refresh_card_list()

    def add_card(self, card_id):
        if self.deck_path is None:
            return
        self.table.add_card(card_id, self.deck_path)
        self.update_card_button(card_id)

    def update_card_button(self, card_id):
        button = self.card_buttons.get(card_id)
        if button:
            button.disabled = card_id in self.table.cards
            button.opacity = 0.45 if button.disabled else 1

    def show_discard(self):
        content = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        if not self.table.discarded:
            content.add_widget(Label(text="La défausse est vide."))
        else:
            scroll = ScrollView()
            entries = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
            entries.bind(minimum_height=entries.setter("height"))
            for card_id in list(self.table.discarded):
                row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
                row.add_widget(Label(text=card_id))
                restore = Button(text="Remettre en jeu", size_hint_x=None, width=dp(150))
                restore.bind(on_release=lambda _btn, value=card_id: self.restore_from_discard(value))
                row.add_widget(restore)
                entries.add_widget(row)
            scroll.add_widget(entries)
            content.add_widget(scroll)
        close = Button(text="Fermer", size_hint_y=None, height=dp(42))
        content.add_widget(close)
        popup = Popup(title="Défausse", content=content, size_hint=(0.45, 0.65))
        close.bind(on_release=popup.dismiss)
        self._discard_popup = popup
        popup.open()

    def restore_from_discard(self, card_id):
        self.table.restore_card(card_id)
        self.update_card_button(card_id)
        if hasattr(self, "_discard_popup"):
            self._discard_popup.dismiss()
        self.show_discard()

    def show_help(self):
        text = ("• Clique sur une carte à gauche pour la poser sur la table.\n"
                "• Fais glisser une carte pour la déplacer.\n"
                "• Utilise deux doigts pour la faire pivoter, ou les boutons ↶ / ↷.\n"
                "• « Retourner » affiche le recto ou le verso.\n"
                "• « Défausser » retire la carte ; le menu Défausse permet de la restaurer.\n"
                "• Une carte déjà sur la table ne peut pas être ajoutée une seconde fois.")
        Popup(title="Aide", content=Label(text=text), size_hint=(0.6, 0.5)).open()


if __name__ == "__main__":
    UnlockTableApp().run()
