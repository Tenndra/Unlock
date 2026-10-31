"""Widget for an individual card on the virtual table."""

from pathlib import Path

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.scatter import Scatter


class MenuIcon(Widget):
    """Small vector icon drawn directly with Kivy canvas instructions."""

    def __init__(self, kind, **kwargs):
        super().__init__(**kwargs)
        self.kind = kind
        self.size_hint = (None, None)
        self.size = (dp(22), dp(22))
        self.bind(pos=self._draw_icon, size=self._draw_icon)
        self._draw_icon()

    def _draw_icon(self, *_):
        self.canvas.clear()
        x, y = self.pos
        w, h = self.size
        with self.canvas:
            if self.kind == "trash":
                Color(1.0, 0.55, 0.16, 1)  # Orange: discard
            else:
                Color(0.35, 0.82, 0.48, 1)  # Green: return to deck
            if self.kind == "trash":
                # Lid, handles and the body of a small wastebasket.
                Line(points=[x + w * .22, y + h * .78, x + w * .78, y + h * .78], width=1.4)
                Line(points=[x + w * .40, y + h * .88, x + w * .60, y + h * .88], width=1.4)
                Line(points=[x + w * .30, y + h * .70, x + w * .36, y + h * .18,
                             x + w * .64, y + h * .18, x + w * .70, y + h * .70], width=1.4)
                Line(points=[x + w * .45, y + h * .60, x + w * .46, y + h * .30], width=1.1)
                Line(points=[x + w * .55, y + h * .60, x + w * .54, y + h * .30], width=1.1)
            else:
                # Return arrow pointing back toward the deck.
                Line(points=[x + w * .78, y + h * .68, x + w * .58, y + h * .84,
                             x + w * .40, y + h * .68], width=1.6)
                Line(points=[x + w * .58, y + h * .82, x + w * .58, y + h * .47,
                             x + w * .42, y + h * .30, x + w * .20, y + h * .30], width=1.6)


class CardOnTable(Scatter):
    """A single physical-style card: move, rotate, resize, flip and discard."""

    card_id = StringProperty("")
    face_up = BooleanProperty(True)

    def __init__(self, card_id, deck_path, on_discard, on_return_to_deck=None, **kwargs):
        super().__init__(**kwargs)
        self.card_id = card_id
        self.deck_path = Path(deck_path)
        self.on_discard_callback = on_discard
        self.on_return_to_deck_callback = on_return_to_deck
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

        from kivy.uix.boxlayout import BoxLayout
        menu_content = BoxLayout(orientation="vertical", spacing=dp(4), padding=dp(4))
        discard_button = Button(
            size_hint=(1, None), height=dp(38),
            background_normal="", background_color=(0.16, 0.19, 0.18, 1),
        )
        discard_row = BoxLayout(orientation="horizontal", spacing=dp(9), padding=(dp(10), 0),
                                size_hint=(None, None))
        discard_row.add_widget(MenuIcon("trash"))
        discard_label = Label(text="Défausser", color=(1, 1, 1, 1),
                              halign="left", valign="middle")
        discard_label.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        discard_row.add_widget(discard_label)
        discard_button.add_widget(discard_row)
        discard_button.bind(pos=lambda button, pos: setattr(discard_row, "pos", pos),
                            size=lambda button, size: setattr(discard_row, "size", size))

        return_button = Button(
            size_hint=(1, None), height=dp(38),
            background_normal="", background_color=(0.16, 0.19, 0.18, 1),
        )
        return_row = BoxLayout(orientation="horizontal", spacing=dp(9), padding=(dp(10), 0),
                               size_hint=(None, None))
        return_row.add_widget(MenuIcon("return"))
        return_label = Label(text="Remettre dans la pioche", color=(1, 1, 1, 1),
                             halign="left", valign="middle")
        return_label.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        return_row.add_widget(return_label)
        return_button.add_widget(return_row)
        return_button.bind(pos=lambda button, pos: setattr(return_row, "pos", pos),
                           size=lambda button, size: setattr(return_row, "size", size))
        menu_content.add_widget(discard_button)
        menu_content.add_widget(return_button)
        popup = Popup(
            content=menu_content,
            size_hint=(None, None),
            size=(dp(198), dp(96)),
            auto_dismiss=True,
            separator_height=0,
            background="",
            background_color=(0.12, 0.14, 0.13, 0.98),
        )
        # Keep the menu fully inside the application window.
        x = min(max(0, pointer_pos[0]), max(0, Window.width - dp(198)))
        y = min(max(0, pointer_pos[1] - dp(96)), max(0, Window.height - dp(96)))
        popup.pos = (x, y)
        discard_button.bind(on_release=lambda *_: self._discard_from_menu(popup))
        return_button.bind(on_release=lambda *_: self._return_to_deck_from_menu(popup))
        self._context_popup = popup
        popup.open()

    def _discard_from_menu(self, popup):
        popup.dismiss()
        self._context_popup = None
        self.discard()

    def _return_to_deck_from_menu(self, popup):
        popup.dismiss()
        self._context_popup = None
        if callable(self.on_return_to_deck_callback):
            self.on_return_to_deck_callback(self)

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
