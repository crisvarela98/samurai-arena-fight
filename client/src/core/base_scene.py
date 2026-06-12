import pygame

from src.ui.button import Button


class BaseScene:
    def __init__(self, game):
        self.game = game
        self.music_button = Button((1088, 42, 150, 46), "", variant="ghost", font_size=18)

    def handle_music_toggle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP and self.music_button.rect.collidepoint(event.pos):
            self.game.toggle_music()
            return True
        return False

    def draw_music_toggle(self, surface):
        self.music_button.text = "MUSICA ON" if self.game.audio.music_enabled else "MUSICA OFF"
        self.music_button.draw(surface)

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass
