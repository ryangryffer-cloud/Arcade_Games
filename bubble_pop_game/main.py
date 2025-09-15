from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from random import randint

class Bubble(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = "assets/bubble.png"
        self.size_hint = (None, None)
        self.size = (64, 64)
        self.x = randint(0, 300)
        self.y = 800
        self.bind(on_touch_down=self.pop_bubble)

    def pop_bubble(self, instance, touch):
        if self.collide_point(*touch.pos):
            sound = SoundLoader.load("assets/pop.wav")
            if sound:
                sound.play()
            self.parent.remove_widget(self)

    def move(self, dt):
        self.y -= 2
        if self.y < -50 and self.parent:
            self.parent.remove_widget(self)

class BubbleGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_interval(self.spawn_bubble, 1.5)

    def spawn_bubble(self, dt):
        bubble = Bubble()
        self.add_widget(bubble)
        Clock.schedule_interval(bubble.move, 1/60)

class BubbleApp(App):
    def build(self):
        return BubbleGame()

if __name__ == "__main__":
    BubbleApp().run()
