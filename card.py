"""Widget for an individual card on the virtual table."""

from pathlib import Path

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.scatter import Scatter


class CardOnTable(Scatter):
    """A single physical-style card: move, rotate, resize, flip and discard."""

    card_id = StringProperty("")
    face_up = BooleanProperty(True)

    def __init__(self, card_id, deck_path, on_discard, **kwargs):
        super().__init__(**kwargs)
        self.card_id = card_id
        self.deck_path = Path(deck_path)
        self.on_discard_callback = on_discard
        self.recto = self.deck_path / f"{card_id}_r.jpg"
        self.verso = self.deck_path / f"{card_id}_v.jpg"
        self.size_hint = (None, None)
        self.size = (dp(280), dp(430))
        self.do_translation = True
        self.do_rotation = True
        self.do_scale = False
        self.auto_bring_to_front = True
        self.rotation = 0
        self._context_popup = None

        self.picture = Image(
            source=str(self.recto),
            fit_mode="fill",
            size_hint=(None, None),
            size=self.size,
            pos=(0, 0),
        )
        self.bind(size=self._sync_picture_size)
        self.add_widget(self.picture)

    def _sync_picture_size(self, *_):
        """Keep the image exactly the size of the card's physical frame."""
        self.picture.size = self.size
        self.picture.pos = (0, 0)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Right-click opens a small context menu next to the pointer.
            if getattr(touch, "button", None) == "right":
                self.show_context_menu(touch.pos)
                return True

            # A double-click flips the card without adding permanent controls.
            if getattr(touch, "is_double_tap", False):
                self.turn_card()
                return True

            # Mouse wheel acts only on the card under the pointer.
            if getattr(touch, "button", None) in ("scrollup", "scrolldown"):
                direction = 1 if touch.button == "scrollup" else -1
                modifiers = (getattr(touch, "modifiers", None)
                             or getattr(Window, "modifiers", [])
                             or [])
                if any(str(key).lower() in ("ctrl", "control") for key in modifiers):
                    self.rotate_card(5 * direction)
                else:
                    factor = 1.1 if direction > 0 else 1 / 1.1
                    self.scale = max(0.45, min(2.5, self.scale * factor))
                return True
        return super().on_touch_down(touch)

    def show_context_menu(self, pointer_pos):
        """Display card actions at the mouse pointer."""
        if self._context_popup is not None:
            self._context_popup.dismiss()

        menu_button = Button(
            text="Défausser",
            size_hint=(None, None),
            size=(dp(150), dp(42)),
            background_normal="",
            background_color=(0.16, 0.19, 0.18, 1),
            color=(1, 1, 1, 1),
        )
        popup = Popup(
            content=menu_button,
            size_hint=(None, None),
            size=(dp(158), dp(50)),
            auto_dismiss=True,
            separator_height=0,
            background="",
            background_color=(0.12, 0.14, 0.13, 0.98),
        )
        # Keep the menu fully inside the application window.
        x = min(max(0, pointer_pos[0]), max(0, Window.width - dp(158)))
        y = min(max(0, pointer_pos[1] - dp(50)), max(0, Window.height - dp(50)))
        popup.pos = (x, y)
        menu_button.bind(on_release=lambda *_: self._discard_from_menu(popup))
        self._context_popup = popup
        popup.open()

    def _discard_from_menu(self, popup):
        popup.dismiss()
        self._context_popup = None
        self.discard()

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


# Load the appearance rules after defining the widget classes used by card.kv.
Builder.load_file(str(Path(__file__).resolve().parent / "card.kv"))
