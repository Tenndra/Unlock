"""Widget for an individual card on the virtual table."""

from pathlib import Path

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter



class CardFrame(BoxLayout):
    """Card border and inner layout; appearance lives in card.kv."""


class CardControls(BoxLayout):
    """Action row below a card."""


class CardActionButton(Button):
    """Secondary action button on a card."""


class CardPrimaryButton(Button):
    """Brass action button on a card."""


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
        # The picture keeps the original 280:430 ratio. The action row sits
        # underneath it and is not counted as part of the printed card.
        self.controls_height = dp(28)
        self.size = (dp(360), dp(360) * 430 / 280 + self.controls_height)
        self.size_hint = (None, None)
        self.do_translation = True
        self.do_rotation = True
        self.do_scale = False
        self.auto_bring_to_front = True
        self.rotation = 0

        # Scatter does not lay out its child automatically: keep the panel
        # synchronized with the Scatter size or the visible card stays small.
        panel = CardFrame(size_hint=(None, None), size=self.size)
        self.bind(size=lambda widget, value: setattr(panel, "size", value))
        self.picture = Image(
            source=str(self.recto),
            fit_mode="contain",
            allow_stretch=True,
            size_hint_y=None,
        )
        self.picture.bind(width=self._sync_picture_height)
        panel.add_widget(self.picture)

        controls = CardControls()
        turn_button = CardPrimaryButton(text="↻  Face")
        turn_button.bind(on_release=lambda *_: self.turn_card())
        discard_button = CardActionButton(text="Jeter")
        discard_button.bind(on_release=lambda *_: self.discard())
        controls.add_widget(turn_button)
        controls.add_widget(discard_button)
        panel.add_widget(controls)
        self.add_widget(panel)

    def _sync_picture_height(self, picture, width):
        """Keep the printed image at its original 280:430 aspect ratio."""
        picture.height = width * 430 / 280

    def on_touch_down(self, touch):
        # Mouse wheel acts only on the card under the pointer.
        # Ctrl + wheel rotates; wheel alone changes this card's visual scale.
        if getattr(touch, "button", None) in ("scrollup", "scrolldown"):
            if self.collide_point(*touch.pos):
                direction = 1 if touch.button == "scrollup" else -1
                # On many Kivy desktop providers, modifier keys are exposed by Window.
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
