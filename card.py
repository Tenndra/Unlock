"""Widget for an individual card on the virtual table."""

from pathlib import Path

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter


class MenuIcon(Widget):
    """Compact vector icon for a context-menu action."""

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
                Color(1.0, 0.55, 0.16, 1)
                Line(points=[x + w*.22, y + h*.78, x + w*.78, y + h*.78], width=1.5)
                Line(points=[x + w*.40, y + h*.88, x + w*.60, y + h*.88], width=1.5)
                Line(points=[x + w*.30, y + h*.70, x + w*.36, y + h*.18,
                             x + w*.64, y + h*.18, x + w*.70, y + h*.70], width=1.5)
                Line(points=[x + w*.45, y + h*.60, x + w*.46, y + h*.30], width=1.2)
                Line(points=[x + w*.55, y + h*.60, x + w*.54, y + h*.30], width=1.2)
            else:
                Color(0.35, 0.82, 0.48, 1)
                Line(points=[x + w*.78, y + h*.68, x + w*.58, y + h*.84,
                             x + w*.40, y + h*.68], width=1.6)
                Line(points=[x + w*.58, y + h*.82, x + w*.58, y + h*.47,
                             x + w*.42, y + h*.30, x + w*.20, y + h*.30], width=1.6)


def _add_menu_button(menu, text, icon_kind, callback):
    button = Button(
        size_hint=(1, None), height=dp(40),
        background_normal="", background_color=(0.16, 0.19, 0.18, 1),
    )
    row = BoxLayout(
        orientation="horizontal", spacing=dp(9),
        padding=(dp(10), 0), size_hint=(None, None),
    )
    row.add_widget(MenuIcon(icon_kind))
    label = Label(text=text, color=(1, 1, 1, 1), halign="left", valign="middle")
    label.bind(size=lambda widget, size: setattr(widget, "text_size", size))
    row.add_widget(label)
    button.add_widget(row)
    button.bind(pos=lambda widget, pos: setattr(row, "pos", pos),
                size=lambda widget, size: setattr(row, "size", size))
    button.bind(on_release=callback)
    menu.add_widget(button)


class ContextMenuLayer(FloatLayout):
    """Window-level menu positioned in absolute window coordinates."""

    def __init__(self, menu, **kwargs):
        super().__init__(**kwargs)
        self.size = Window.size
        self.size_hint = (None, None)
        self.menu = menu
        self.add_widget(menu)

    def on_touch_down(self, touch):
        if not self.menu.collide_point(*touch.pos):
            Window.remove_widget(self)
            return False
        return super().on_touch_down(touch)


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
        """Show a lightweight menu directly on the application window."""
        if self._context_popup is not None:
            Window.remove_widget(self._context_popup)
            self._context_popup = None

        menu = BoxLayout(
            orientation="vertical",
            spacing=dp(4),
            padding=dp(4),
            size_hint=(None, None),
            size=(dp(210), dp(92)),
        )
        _add_menu_button(
            menu, "Défausser", "trash",
            lambda *_: self._discard_from_menu(self._context_popup),
        )
        _add_menu_button(
            menu, "Remettre dans la pioche", "return",
            lambda *_: self._return_to_deck_from_menu(self._context_popup),
        )

        # This is a normal widget attached to Window, not a Popup: Kivy
        # therefore cannot recenter it. touch.pos is already in window space.
        x = min(max(0, pointer_pos[0]), max(0, Window.width - menu.width))
        y = pointer_pos[1] - menu.height
        if y < 0:
            y = min(pointer_pos[1], Window.height - menu.height)
        y = min(max(0, y), max(0, Window.height - menu.height))

        layer = ContextMenuLayer(menu)
        menu.pos = (x, y)
        Window.add_widget(layer)
        self._context_popup = layer


    def _close_context_menu(self, layer):
        if layer is not None and layer.parent is Window:
            Window.remove_widget(layer)
        if self._context_popup is layer:
            self._context_popup = None

    def _discard_from_menu(self, layer):
        self._close_context_menu(layer)
        self.discard()

    def _return_to_deck_from_menu(self, layer):
        self._close_context_menu(layer)
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
