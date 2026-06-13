import json
from pathlib import Path

import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GOLD, LIGHT, RED
from src.ui.button import Button
from src.ui.menu_theme import draw_backdrop, draw_chip, draw_footer, draw_panel, get_font


def _wrap(text, font, width):
    lines = []
    current = ""
    for word in text.split():
        candidate = word if not current else f"{current} {word}"
        if font.size(candidate)[0] <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class StoryMissionSelectScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        root = Path(__file__).resolve().parents[2]
        self.missions = json.loads((root / "data" / "story" / "missions.json").read_text(encoding="utf-8"))
        self.background = self.game.assets.load_image(
            "assets/arenas/coliseo_de_acero_bg.png",
            size=(self.game.settings["screen_width"], self.game.settings["screen_height"]),
        )
        self.start_button = Button((866, 562, 272, 58), "INICIAR MISION", variant="primary", font_size=23)
        self.back_button = Button((42, 42, 140, 46), "MAPA", variant="ghost", font_size=20)

    def _mission(self):
        number = int(self.game.shared.get("story_mission", 1))
        return next(item for item in self.missions if item["number"] == number)

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONUP:
            return
        if self.back_button.rect.collidepoint(event.pos):
            self.game.go("story_map")
        elif self.start_button.rect.collidepoint(event.pos):
            mission = self._mission()
            self.game.shared["story_fight_index"] = 0
            self.game.shared["story_cutscene_id"] = mission["intro_cutscene"]
            if mission.get("ftue"):
                self.game.shared["story_episode_elapsed"] = 0.0
                self.game.shared["story_episode_active"] = True
            self.game.go("story_cutscene")

    def draw(self, surface):
        draw_backdrop(surface, self.background, overlay_color=(5, 5, 8, 182))
        self.back_button.draw(surface)
        mission = self._mission()
        draw_panel(surface, pygame.Rect(120, 112, 1040, 524), title=f"MISION {mission['number']} - ACTO 1")
        title = get_font("display", 54, bold=True).render(mission["title"].upper(), True, GOLD)
        surface.blit(title, (170, 182))
        body_font = get_font("body", 24)
        for index, line in enumerate(_wrap(mission["summary"], body_font, 660)):
            surface.blit(body_font.render(line, True, LIGHT), (174, 270 + index * 32))
        draw_chip(surface, pygame.Rect(174, 382, 170, 34), f"{len(mission['fights'])} PELEAS", accent=RED)
        draw_chip(surface, pygame.Rect(356, 382, 200, 34), f"RECOMPENSA {mission['reward_coins']}")
        if mission.get("ftue"):
            draw_chip(surface, pygame.Rect(568, 382, 340, 34), "EPISODIO JUGABLE - MAX. 2 MIN", accent=(80, 180, 95))
        note = "Kenji es el unico protagonista del modo historia."
        surface.blit(body_font.render(note, True, LIGHT), (174, 468))
        self.start_button.draw(surface, selected=True)
        draw_footer(surface, "Las escenas narrativas pueden saltarse desde la esquina superior derecha")
