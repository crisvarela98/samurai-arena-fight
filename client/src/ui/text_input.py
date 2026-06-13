import pygame

from src.core.constants import GOLD, LIGHT, RED
from src.ui.menu_theme import EBONY, MIST, get_font


class TextInput:
    def __init__(self, rect, placeholder="", password=False, max_length=64):
        self.rect = pygame.Rect(rect)
        self.placeholder = placeholder
        self.text = ""
        self.focused = False
        self.password = password
        self.max_length = max_length
        self.font = get_font("body", 26, bold=True)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.focused = self.rect.collidepoint(event.pos)
            if self.focused:
                pygame.key.start_text_input()
            else:
                pygame.key.stop_text_input()
        elif event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.focused = False
                pygame.key.stop_text_input()
            elif len(event.unicode) == 1 and len(self.text) < self.max_length:
                self.text += event.unicode

    def draw(self, surface):
        glow = pygame.Surface((self.rect.width + 24, self.rect.height + 24), pygame.SRCALPHA)
        glow_color = GOLD if self.focused else RED
        pygame.draw.rect(glow, (*glow_color, 42), glow.get_rect(), border_radius=20)
        surface.blit(glow, (self.rect.x - 12, self.rect.y - 4))

        body = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(body, (*EBONY, 236), body.get_rect(), border_radius=14)
        pygame.draw.rect(body, (255, 255, 255, 12), body.get_rect(), 1, border_radius=14)
        pygame.draw.rect(body, (*(GOLD if self.focused else (108, 112, 122)), 255), body.get_rect(), 2, border_radius=14)
        pygame.draw.rect(body, (255, 255, 255, 16), pygame.Rect(12, 10, self.rect.width - 24, 10), border_radius=999)
        surface.blit(body, self.rect.topleft)

        value = ("*" * len(self.text) if self.password and self.text else self.text) or self.placeholder
        color = LIGHT if self.text else MIST
        label = self.font.render(value, True, color)
        surface.blit(label, (self.rect.x + 16, self.rect.y + 10))
