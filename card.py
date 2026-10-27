"""Widget for an individual card on the virtual table."""

from pathlib import Path

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter


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
        panel = BoxLayout(orientation="vertical", spacing=dp(3), padding=dp(3),
                          size_hint=(None, None), size=self.size)
        with panel.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.055, 0.065, 0.07, 1)
            self._card_frame = Rectangle(pos=panel.pos, size=panel.size)
        panel.bind(pos=lambda w, *_: setattr(self._card_frame, "pos", w.pos),
                   size=lambda w, *_: setattr(self._card_frame, "size", w.size))
        self.bind(size=lambda widget, value: setattr(panel, "size", value))
        self.picture = Image(
            source=str(self.recto),
            fit_mode="contain",
            allow_stretch=True,
        )
        panel.add_widget(self.picture)

        controls = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(3))
        turn_button = Button(text="↻  Face", font_size=dp(10), padding=(dp(1), 0),
                             background_normal="", background_down="",
                             background_color=(0.78, 0.61, 0.31, 1),
                             color=(0.055, 0.075, 0.09, 1), bold=True)
        turn_button.bind(on_release=lambda *_: self.turn_card())
        discard_button = Button(text="Jeter", font_size=dp(10), padding=(dp(1), 0),
                                background_normal="", background_down="",
                                background_color=(0.20, 0.23, 0.24, 1),
                                color=(0.94, 0.92, 0.85, 1))
        discard_button.bind(on_release=lambda *_: self.discard())
        controls.add_widget(turn_button)
        controls.add_widget(discard_button)
        panel.add_widget(controls)
        self.add_widget(panel)

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
