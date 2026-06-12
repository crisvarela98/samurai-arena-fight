import pygame

from src.core.base_scene import BaseScene
from src.core.constants import LIGHT
from src.ui.button import Button
from src.ui.menu_theme import draw_panel, get_font


class PauseMenuScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.buttons = [
            Button((500, 252, 280, 54), "CONTINUAR", variant="primary", font_size=24),
            Button((500, 322, 280, 54), "REINICIAR", font_size=24),
            Button((500, 392, 280, 54), "OPCIONES", font_size=24),
            Button((500, 462, 280, 54), "SALIR AL MENU", variant="danger", font_size=24),
        ]
        self.title_font = get_font("heading", 34, bold=True)
        self.body_font = get_font("body", 20)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.scene_manager.pop()
        if event.type == pygame.MOUSEBUTTONUP:
            if self.buttons[0].rect.collidepoint(event.pos):
                self.game.scene_manager.pop()
            elif self.buttons[3].rect.collidepoint(event.pos):
                self.game.scene_manager.pop()
                self.game.go("menu")

    def draw(self, surface):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 184))
        surface.blit(overlay, (0, 0))
        panel_rect = pygame.Rect(396, 168, 488, 394)
        draw_panel(surface, panel_rect, title="MENU DE PAUSA")
        title = self.title_font.render("COMBATE DETENIDO", True, LIGHT)
        surface.blit(title, title.get_rect(center=(640, 228)))
        body = self.body_font.render("Retoma la pelea o vuelve al menu principal.", True, LIGHT)
        surface.blit(body, body.get_rect(center=(640, 264)))
        for index, button in enumerate(self.buttons):
            button.draw(surface, selected=index == 0)
