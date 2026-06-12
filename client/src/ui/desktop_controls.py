from src.core.constants import LIGHT
from src.core.input_manager import DESKTOP_HINT_TEXT


class DesktopControls:
    def draw_hint(self, surface):
        import pygame

        font = pygame.font.SysFont("arial", 18)
        text = font.render(DESKTOP_HINT_TEXT, True, LIGHT)
        surface.blit(text, (20, 688))
