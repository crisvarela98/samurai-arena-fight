import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GOLD, LIGHT
from src.ui.button import Button
from src.ui.menu_theme import draw_panel


class MainMenuScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.music_button.rect = pygame.Rect(1008, 34, 202, 44)
        self.background = self.game.assets.load_image(
            "assets/ui/menu_main_bg_v2.png",
            size=(self.game.settings["screen_width"], self.game.settings["screen_height"]),
        )
        self.button_actions = ["quick", "story", "online", "options"]
        self.buttons = [
            Button((876, 214, 286, 64), "JUEGO RAPIDO", variant="primary"),
            Button((876, 298, 286, 64), "MODO HISTORIA"),
            Button((876, 382, 286, 64), "ONLINE", variant="primary"),
            Button((876, 466, 286, 64), "OPCIONES"),
        ]

    def handle_event(self, event):
        if event.type not in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP}:
            return
        if event.type == pygame.MOUSEBUTTONUP and self.handle_music_toggle_event(event):
            return

        for action, button in zip(self.button_actions, self.buttons):
            if button.handle_event(event):
                self._trigger_action(action)
                return

    def _trigger_action(self, action):
        if action == "quick":
            self.game.shared["match_mode"] = "local"
            self.game.shared["menu_entry"] = "quick"
            self.game.go("character")
        elif action == "story":
            self.game.shared["match_mode"] = "local"
            self.game.shared["menu_entry"] = "story"
            self.game.go("character")
        elif action == "online":
            self.game.shared["match_mode"] = "online"
            self.game.shared["menu_entry"] = "online"
            self.game.go("character")
        elif action == "options":
            self.game.go("platform")

    def draw(self, surface):
        surface.blit(self.background, (0, 0))

        ambience = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        ambience.fill((4, 5, 8, 40))
        surface.blit(ambience, (0, 0))

        right_shadow = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for step in range(7):
            x = 748 + step * 34
            alpha = 26 + step * 16
            pygame.draw.rect(right_shadow, (4, 4, 7, alpha), pygame.Rect(x, 0, 1280 - x, 720))
        surface.blit(right_shadow, (0, 0))

        menu_panel = pygame.Rect(820, 112, 398, 468)
        draw_panel(surface, menu_panel, accent=GOLD, fill=(8, 10, 14, 204))

        border = pygame.Surface((menu_panel.width, menu_panel.height), pygame.SRCALPHA)
        pygame.draw.rect(border, (255, 255, 255, 14), border.get_rect(), 1, border_radius=22)
        pygame.draw.line(border, (*LIGHT, 28), (38, 78), (menu_panel.width - 38, 78), 1)
        surface.blit(border, menu_panel.topleft)

        self.draw_music_toggle(surface)

        for index, button in enumerate(self.buttons):
            button.draw(surface, selected=index in {0, 2})
