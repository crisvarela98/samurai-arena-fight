import json
from pathlib import Path

import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GOLD, LIGHT
from src.ui.button import Button
from src.ui.menu_theme import blit_contain, draw_panel, get_font


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


class StoryCutsceneScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        root = Path(__file__).resolve().parents[2]
        cutscenes = json.loads((root / "data" / "story" / "cutscenes.json").read_text(encoding="utf-8"))
        self.cutscenes = {item["id"]: item for item in cutscenes}
        self.skip_button = Button((1090, 30, 158, 38), "SALTAR VIDEO", variant="ghost", font_size=16)
        self.panel_index = 0
        self.panel_timer = 0.0
        self.cutscene = None
        self.panel_images = {}

    def on_enter(self):
        cutscene_id = self.game.shared.get("story_cutscene_id", "prologue")
        self.cutscene = self.cutscenes[cutscene_id]
        self.panel_index = 0
        self.panel_timer = 0.0
        self.panel_images = {}
        for panel in self.cutscene["panels"]:
            path = panel.get("image")
            if path and path not in self.panel_images:
                self.panel_images[path] = self.game.assets.load_image(path, trim_alpha=path.endswith("portrait.png"))

    def _finish(self):
        next_scene = self.cutscene.get("next_scene", "story_map")
        mission_number = self.game.shared.get("story_mission", 1)
        if next_scene == "memory_fragment":
            missions_path = Path(__file__).resolve().parents[2] / "data" / "story" / "missions.json"
            missions = json.loads(missions_path.read_text(encoding="utf-8"))
            mission = next(item for item in missions if item["number"] == mission_number)
            self.game.shared["memory_fragment_id"] = mission.get("memory_fragment")
            self.game.shared["memory_next_scene"] = "menu" if mission_number == 1 else "story_map"
        if next_scene == "menu":
            self.game.shared["story_episode_active"] = False
        self.game.go(next_scene)

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONUP:
            return
        if self.cutscene.get("skippable", True) and self.skip_button.rect.collidepoint(event.pos):
            self._finish()
            return
        self.panel_index += 1
        self.panel_timer = 0.0
        if self.panel_index >= len(self.cutscene["panels"]):
            self._finish()

    def update(self, dt):
        if self.game.shared.get("story_episode_active"):
            self.game.shared["story_episode_elapsed"] = self.game.shared.get("story_episode_elapsed", 0.0) + dt
        self.panel_timer += dt
        panel = self.cutscene["panels"][self.panel_index]
        if self.panel_timer >= float(panel.get("duration", 3.0)):
            self.panel_index += 1
            self.panel_timer = 0.0
            if self.panel_index >= len(self.cutscene["panels"]):
                self._finish()

    def _draw_rain(self, surface):
        tick = pygame.time.get_ticks()
        for index in range(72):
            x = int((index * 97 + tick * 0.19) % surface.get_width())
            y = int((index * 61 + tick * 0.43) % surface.get_height())
            pygame.draw.line(surface, (150, 174, 194, 150), (x, y), (x - 7, y + 20), 1)

    def draw(self, surface):
        surface.fill((0, 0, 0))
        panel = self.cutscene["panels"][self.panel_index]
        image = self.panel_images.get(panel.get("image"))
        if image:
            if "portrait" in panel.get("image", "") or "sheet" in panel.get("image", ""):
                blit_contain(surface, image, pygame.Rect(180, 80, 920, 470), bottom_align=True)
            else:
                surface.blit(pygame.transform.smoothscale(image, surface.get_size()), (0, 0))
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 86))
        surface.blit(shade, (0, 0))
        if panel.get("sound") == "rain":
            self._draw_rain(surface)
        pygame.draw.rect(surface, (236, 226, 208), pygame.Rect(40, 38, 1200, 4))
        draw_panel(surface, pygame.Rect(80, 504, 1120, 164), title=panel.get("speaker", "NARRADOR"))
        font = get_font("body", 27)
        for index, line in enumerate(_wrap(panel.get("text", ""), font, 1020)):
            surface.blit(font.render(line, True, LIGHT), (126, 566 + index * 34))
        counter = get_font("tiny", 17, bold=True).render(f"{self.panel_index + 1}/{len(self.cutscene['panels'])}", True, GOLD)
        surface.blit(counter, (100, 650))
        if self.cutscene.get("skippable", True):
            self.skip_button.draw(surface)
