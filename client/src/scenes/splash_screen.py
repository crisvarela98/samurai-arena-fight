from pathlib import Path

import pygame

from src.core.base_scene import BaseScene
from src.ui.menu_theme import blit_contain


class SplashScreenScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.timer = 0.0
        self.duration = 2.0
        self.root = Path(self.game.client_dir)
        self.studio_logo = self._load_optional_logo("assets/ui/logos/studio_logo.png")
        self.game_logo = self._load_optional_logo("assets/ui/logos/game_logo.png")
        self.placeholder_font = pygame.font.SysFont("arial", 22, bold=True)

    def _load_optional_logo(self, relative_path):
        asset_path = self.root / relative_path
        if not asset_path.exists():
            return None
        return self.game.assets.load_image(relative_path, trim_alpha=True)

    def on_enter(self):
        self.timer = 0.0

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.duration:
            if self.game.progress.data.get("first_time_completed"):
                self.game.go("menu")
            else:
                self.game.go("story_intro")

    def _draw_logo(self, surface, rect, logo, label):
        if logo is not None:
            blit_contain(surface, logo, rect)
            return

        pygame.draw.rect(surface, (70, 70, 70), rect, 2, border_radius=18)
        text = self.placeholder_font.render(label, True, (220, 220, 220))
        surface.blit(text, text.get_rect(center=rect.center))

    def draw(self, surface):
        surface.fill((0, 0, 0))
        self._draw_logo(surface, pygame.Rect(400, 120, 480, 140), self.studio_logo, "studio_logo.png")
        self._draw_logo(surface, pygame.Rect(200, 300, 880, 220), self.game_logo, "game_logo.png")
