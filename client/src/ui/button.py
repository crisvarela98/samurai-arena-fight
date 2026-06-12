import pygame

from src.core.constants import GOLD, LIGHT, RED
from src.ui.menu_theme import CHARCOAL, CRIMSON, EBONY, MIST, get_font


class Button:
    def __init__(self, rect, text, action=None, font_size=28, active=True, variant="secondary"):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.active = active
        self.variant = variant
        self.font = get_font("heading", font_size, bold=True)
        self.pressed = False

    def _palette(self, selected, hovered):
        if self.variant == "danger":
            base = (92, 28, 28)
            border = RED
            highlight = (185, 72, 72)
        elif self.variant == "ghost":
            base = (22, 24, 30)
            border = (108, 112, 122)
            highlight = (210, 210, 214)
        elif selected or self.variant == "primary":
            base = CRIMSON
            border = GOLD
            highlight = (255, 214, 140)
        else:
            base = EBONY
            border = (112, 88, 62)
            highlight = (146, 152, 170)
        if hovered:
            base = tuple(min(255, channel + 18) for channel in base)
        return base, border, highlight

    def draw(self, surface, selected=False):
        hovered = self.active and self.rect.collidepoint(pygame.mouse.get_pos())
        base, border, highlight = self._palette(selected, hovered)
        shadow_rect = self.rect.move(0, 8)
        shadow = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 80), shadow.get_rect(), border_radius=16)
        surface.blit(shadow, shadow_rect.topleft)

        body = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(body, (*base, 242), body.get_rect(), border_radius=16)
        pygame.draw.rect(body, (255, 255, 255, 18), body.get_rect(), 1, border_radius=16)
        pygame.draw.rect(body, (*border, 255), body.get_rect(), 2, border_radius=16)
        pygame.draw.rect(body, (*highlight, 54), pygame.Rect(12, 10, self.rect.width - 24, 14), border_radius=999)
        pygame.draw.line(body, (*border, 255), (18, self.rect.height - 12), (self.rect.width - 18, self.rect.height - 12), 2)
        surface.blit(body, self.rect.topleft)

        text_color = LIGHT if self.active else MIST
        if self.pressed:
            text_color = GOLD if self.active else MIST
        label = self.font.render(self.text, True, text_color)
        surface.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if not self.active:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.pressed = True
            return True
        if event.type == pygame.MOUSEBUTTONUP:
            clicked = self.pressed and self.rect.collidepoint(event.pos)
            self.pressed = False
            return clicked
        return False
