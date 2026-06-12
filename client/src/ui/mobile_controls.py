import pygame

from src.core.constants import GOLD, RED, LIGHT


class MobileControls:
    def __init__(self):
        self.buttons = {
            "up": pygame.Rect(110, 480, 80, 80),
            "left": pygame.Rect(24, 560, 80, 80),
            "right": pygame.Rect(196, 560, 80, 80),
            "down": pygame.Rect(110, 640, 80, 80),
            "light": pygame.Rect(1100, 520, 80, 80),
            "heavy": pygame.Rect(1190, 460, 80, 80),
            "kick": pygame.Rect(1000, 560, 80, 80),
            "block": pygame.Rect(1090, 620, 80, 80),
            "dodge": pygame.Rect(1180, 620, 80, 80),
            "pause": pygame.Rect(600, 640, 80, 60),
        }
        self.button_labels = {
            "up": "SAL",
            "left": "IZQ",
            "right": "DER",
            "down": "ABA",
            "light": "GOL",
            "heavy": "SUP",
            "kick": "PAT",
            "block": "BLQ",
            "dodge": "ESQ",
            "pause": "II",
        }
        self.font = pygame.font.SysFont("arial", 19, bold=True)

    def draw(self, surface):
        for action, rect in self.buttons.items():
            pygame.draw.ellipse(surface, (28, 28, 32), rect)
            pygame.draw.ellipse(surface, GOLD if action in {"light", "heavy", "up"} else RED, rect, 2)
            label = self.button_labels[action]
            text = self.font.render(label, True, LIGHT)
            surface.blit(text, text.get_rect(center=rect.center))

    def action_from_pos(self, pos):
        for action, rect in self.buttons.items():
            if rect.collidepoint(pos):
                return action
        return None
