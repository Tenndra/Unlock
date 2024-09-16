from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.image import Image
from kivy.uix.scatterlayout import ScatterLayout


class CardLayout(ScatterLayout):
    current_face = StringProperty()
    card_image = ObjectProperty()
    current_rotation = 0

    def __init__(self, card_name, deck, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.recto = "ressources/decks/" + deck + '/' + card_name + '_r.jpg'
        self.verso = "ressources/decks/" + deck + '/' + card_name + '_v.jpg'
        self.current_face = self.recto
        self.size_hint_x = 0.20
        self.size_hint_y = 0.5

    def turn(self):
        if self.current_face == self.recto:
            self.current_face = self.verso
        else:
            self.current_face = self.recto

    def rotate_left(self):
        self.card_image.rotation += 45

    def rotate_right(self):
        self.card_image.rotation -= 45

    def delete_card(self):
        self.callback(self)


class CardImage(Image):
    def on_touch_down(self, touch):
        image_parent = self.parent.parent.parent.parent.parent  # A améliorer
        image = ZoomImage(image_parent.current_face)
        image.size_hint = (1, 1)
        target = image_parent.parent.parent
        target.add_widget(image)


class ZoomImage(ScatterLayout):
    def __init__(self, source, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Image(source=source))

    def on_touch_down(self, touch):
        self.parent.remove_widget(self)
