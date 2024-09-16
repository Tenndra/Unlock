from kivy.uix.boxlayout import BoxLayout


class ZoomLayout(BoxLayout):
    def on_touch_down(self, touch):
        print('close')
