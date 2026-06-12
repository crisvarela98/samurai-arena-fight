import pygame

from src.core.base_scene import BaseScene
from src.core.input_manager import MOBILE_CONTROL_ROWS
from src.core.constants import GOLD, LIGHT
from src.ui.button import Button
from src.ui.menu_theme import draw_backdrop, draw_chip, draw_footer, draw_panel, draw_stage_label, get_font


class PlatformSelectScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.background = self.game.assets.load_image(
            "assets/ui/menu_armory_bg.png",
            size=(self.game.settings["screen_width"], self.game.settings["screen_height"]),
        )
        self.back_button = Button((42, 42, 140, 46), "VOLVER", variant="ghost", font_size=20)
        self.title_font = get_font("heading", 26, bold=True)
        self.body_font = get_font("body", 18)
        self.row_key_font = get_font("tiny", 15, bold=True)
        self.row_text_font = get_font("body", 17)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            if self.handle_music_toggle_event(event):
                return
            if self.back_button.rect.collidepoint(event.pos):
                self.game.go("menu")

    def _draw_control_rows(self, surface, rows, x, y, width, accent):
        for index, (key_label, action_label) in enumerate(rows):
            row_rect = pygame.Rect(x, y + index * 33, width, 28)
            row = pygame.Surface(row_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(row, (11, 14, 20, 196), row.get_rect(), border_radius=10)
            pygame.draw.rect(row, (255, 255, 255, 12), row.get_rect(), 1, border_radius=10)
            surface.blit(row, row_rect.topleft)

            key_rect = pygame.Rect(row_rect.x + 10, row_rect.y + 4, 132, 20)
            pygame.draw.rect(surface, (18, 20, 26), key_rect, border_radius=999)
            pygame.draw.rect(surface, accent, key_rect, 2, border_radius=999)
            key_text = self.row_key_font.render(key_label, True, LIGHT)
            label_text = self.row_text_font.render(action_label, True, LIGHT)
            surface.blit(key_text, key_text.get_rect(center=key_rect.center))
            surface.blit(label_text, (row_rect.x + 154, row_rect.y + 4))

    def draw(self, surface):
        draw_backdrop(surface, self.background, overlay_color=(8, 7, 10, 126))
        self.back_button.draw(surface)
        self.draw_music_toggle(surface)
        draw_stage_label(surface, "OPCIONES / CONTROLES", "Por ahora la interfaz visible esta centrada en Android.", x=206, y=54)

        info_rect = pygame.Rect(54, 124, 1172, 100)
        mobile_rect = pygame.Rect(180, 244, 920, 418)
        draw_panel(surface, info_rect, title="MODO ACTUAL")
        draw_panel(surface, mobile_rect, title="CONTROLES ANDROID")

        draw_chip(surface, pygame.Rect(88, 164, 140, 30), "FOCO ANDROID")
        draw_chip(surface, pygame.Rect(240, 164, 220, 30), "CONTROLES TACTILES", accent=(80, 180, 95))
        info_text = self.body_font.render("La presentacion actual prioriza combate y flujo de uso en celular.", True, LIGHT)
        surface.blit(info_text, (486, 168))

        active_mobile = self.title_font.render("Esquema visible para Android", True, LIGHT)
        surface.blit(active_mobile, (212, 296))
        pygame.draw.line(surface, GOLD, (212, 328), (1068, 328), 2)

        self._draw_control_rows(surface, MOBILE_CONTROL_ROWS, 212, 342, 856, GOLD)

        draw_footer(surface, "Flujo visual enfocado en Android por ahora")
