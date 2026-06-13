import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GOLD, LIGHT
from src.ui.menu_theme import draw_backdrop, draw_panel, get_font


class StoryIntroScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.background = self.game.assets.load_image(
            "assets/arenas/templo_en_llamas_bg.png",
            size=(self.game.settings["screen_width"], self.game.settings["screen_height"]),
        )
        self.pending_start = False

    def on_enter(self):
        self.pending_start = True
        self.game.shared["story_episode_elapsed"] = 0.0
        self.game.shared["story_episode_active"] = True

    def update(self, dt):
        if not self.pending_start:
            return
        self.pending_start = False
        self.game.shared["story_mission"] = 1
        self.game.shared["story_fight_index"] = 0
        self.game.shared["story_cutscene_id"] = "prologue"
        self.game.go("story_cutscene")

    def draw(self, surface):
        draw_backdrop(surface, self.background, overlay_color=(0, 0, 0, 205))
        draw_panel(surface, pygame.Rect(250, 194, 780, 310), title="ACTO 1")
        title = get_font("display", 72, bold=True).render("EL DESPERTAR", True, GOLD)
        detail = get_font("body", 25).render("Entre los muertos comienza la historia de Kenji.", True, LIGHT)
        surface.blit(title, title.get_rect(center=(640, 320)))
        surface.blit(detail, detail.get_rect(center=(640, 398)))
