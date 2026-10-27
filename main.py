"""Application entry point and main user interface."""

from pathlib import Path

from kivy.config import Config
Config.set("graphics", "fullscreen", "auto")
Config.set("graphics", "resizable", "1")
Config.set("input", "mouse", "mouse,multitouch_on_demand")

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget

from table import TableSurface


ROOT = Path(__file__).resolve().parent
DECKS_DIR = ROOT / "ressources" / "decks"
# Palette: dark slate, warm ivory and restrained brass accents.
INK = (0.055, 0.075, 0.09, 1)
PANEL = (0.09, 0.12, 0.14, 1)
PANEL_LIGHT = (0.14, 0.18, 0.20, 1)
BRASS = (0.78, 0.61, 0.31, 1)
IVORY = (0.94, 0.92, 0.85, 1)
MUTED = (0.66, 0.70, 0.69, 1)
Window.clearcolor = INK


def readable_name(path: Path) -> str:
    return path.stem[:-2]


class UnlockTableApp(App):
    title = "Unlock — table virtuelle"

    def build(self):
        self.deck_path = None
        self.card_ids = []
        self.card_buttons = {}
        root = BoxLayout(orientation="vertical", spacing=dp(2), padding=dp(5))
        with root.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*INK)
            self._root_bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda w, *_: setattr(self._root_bg, "pos", w.pos),
                  size=lambda w, *_: setattr(self._root_bg, "size", w.size))
        root.add_widget(self.build_toolbar())

        body = BoxLayout(spacing=dp(5))
        # A narrower sidebar leaves more room for the play area.
        sidebar = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(180),
                            padding=dp(7), spacing=dp(5))
        with sidebar.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*PANEL)
            self._sidebar_bg = Rectangle(pos=sidebar.pos, size=sidebar.size)
        sidebar.bind(pos=lambda w, *_: setattr(self._sidebar_bg, "pos", w.pos),
                     size=lambda w, *_: setattr(self._sidebar_bg, "size", w.size))
        sidebar.add_widget(Label(text="[b]CARTES DU PAQUET[/b]", markup=True,
                                 size_hint_y=None, height=dp(28), color=BRASS,
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
        bar = BoxLayout(size_hint_y=None, height=dp(58), padding=(dp(12), dp(7)),
                        spacing=dp(9))
        with bar.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*PANEL)
            self._toolbar_bg = Rectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda w, *_: setattr(self._toolbar_bg, "pos", w.pos),
                 size=lambda w, *_: setattr(self._toolbar_bg, "size", w.size))
        title = Label(text="[b]UNLOCK[/b]  [color=#C79C50]•[/color]  TABLE VIRTUELLE",
                      markup=True, color=IVORY, bold=True, size_hint_x=None,
                      width=dp(280), font_size=dp(16), halign="left", valign="middle")
        title.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        bar.add_widget(title)
        decks = self.available_decks()
        self.deck_spinner = Spinner(text=decks[0] if decks else "Aucun paquet",
                                    values=decks, size_hint_x=None, width=dp(280),
                                    background_normal="", background_color=PANEL_LIGHT,
                                    color=IVORY, font_size=dp(13))
        self.deck_spinner.bind(text=lambda _spinner, value: self.load_deck(value))
        bar.add_widget(self.deck_spinner)
        bar.add_widget(Widget())
        help_button = Button(text="?  Aide", size_hint_x=None, width=dp(90),
                             background_normal="", background_down="",
                             background_color=PANEL_LIGHT, color=IVORY,
                             font_size=dp(12))
        help_button.bind(on_release=lambda *_: self.show_help())
        bar.add_widget(help_button)
        discard_button = Button(text="♧  Défausse", size_hint_x=None, width=dp(120),
                                background_normal="", background_down="",
                                background_color=BRASS, color=INK,
                                font_size=dp(12), bold=True)
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
                            padding=(0, 0), background_normal="",
                            background_down="", background_color=PANEL_LIGHT,
                            color=IVORY)
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
                "• Molette au-dessus d’une carte : agrandir ou réduire cette carte.\n"
                "• Ctrl + molette au-dessus d’une carte : la faire pivoter.\n"
                "• « Face » affiche le recto ou le verso.\n"
                "• « Jeter » retire la carte ; le menu Défausse permet de la restaurer.\n"
                "• Une carte déjà sur la table ne peut pas être ajoutée une seconde fois.")
        Popup(title="Aide", content=Label(text=text), size_hint=(0.6, 0.5)).open()


if __name__ == "__main__":
    UnlockTableApp().run()
