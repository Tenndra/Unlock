"""Reusable widget classes whose appearance is defined in KV files."""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label


class AppRoot(BoxLayout):
    """Main application container."""


class ToolbarPanel(BoxLayout):
    """Top toolbar panel."""


class SidebarPanel(BoxLayout):
    """Deck sidebar panel."""


class BrassButton(Button):
    """Primary brass-colored action button."""


class DarkButton(Button):
    """Secondary dark action button."""


class HelpButton(Button):
    """Toolbar help action."""


class DeckCardButton(Button):
    """Square button representing a card in the deck."""


class SectionTitle(Label):
    """Small uppercase panel heading."""


class ToolbarTitle(Label):
    """Application title shown in the toolbar."""


class CardFrame(BoxLayout):
    """Dark frame surrounding the card image and controls."""


class CardControls(BoxLayout):
    """Horizontal action row below a card image."""


class CardActionButton(Button):
    """Compact button used on a card."""
