import json
from pathlib import Path

import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GOLD, GREEN, LIGHT
from src.ui.button import Button
from src.ui.menu_theme import draw_backdrop, draw_chip, draw_footer, draw_panel, get_font


class StoryMapScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        root = Path(__file__).resolve().parents[2]
        self.missions = json.loads((root / "data" / "story" / "missions.json").read_text(encoding="utf-8"))
        self.background = self.game.assets.load_image(
            "assets/ui/menu_main_bg.png",
            size=(self.game.settings["screen_width"], self.game.settings["screen_height"]),
        )
        self.back_button = Button((42, 42, 140, 46), "VOLVER", variant="ghost", font_size=20)
        self.mission_buttons = []
        positions = [(112, 188), (330, 296), (552, 194), (756, 326), (972, 210), (1040, 456)]
        for mission, position in zip(self.missions, positions):
            self.mission_buttons.append((mission, Button((*position, 174, 72), f"MISION {mission['number']}", font_size=20)))

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONUP:
            return
        if self.back_button.rect.collidepoint(event.pos):
            self.game.go("menu")
            return
        for mission, button in self.mission_buttons:
            if button.rect.collidepoint(event.pos) and self.game.progress.mission_unlocked(mission["number"]):
                self.game.shared["story_mission"] = mission["number"]
                self.game.go("story_mission_select")
                return

    def draw(self, surface):
        draw_backdrop(surface, self.background, overlay_color=(5, 7, 10, 174))
        self.back_button.draw(surface)
        draw_panel(surface, pygame.Rect(60, 110, 1160, 526), title="ACTO 1 - EL DESPERTAR")
        pygame.draw.lines(surface, (112, 76, 54), False, [button.rect.center for _, button in self.mission_buttons], 5)
        completed = set(self.game.progress.data.get("completed_missions", []))
        for mission, button in self.mission_buttons:
            unlocked = self.game.progress.mission_unlocked(mission["number"])
            button.active = unlocked
            button.draw(surface, selected=mission["number"] in completed)
            status = "COMPLETA" if mission["number"] in completed else "DISPONIBLE" if unlocked else "BLOQUEADA"
            color = GREEN if mission["number"] in completed else GOLD if unlocked else (92, 92, 98)
            draw_chip(surface, pygame.Rect(button.rect.x + 12, button.rect.bottom + 8, 150, 26), status, accent=color)
            label = get_font("tiny", 16, bold=True).render(mission["title"].upper(), True, LIGHT if unlocked else (110, 110, 116))
            surface.blit(label, label.get_rect(center=(button.rect.centerx, button.rect.y - 16)))
        coins = get_font("heading", 22, bold=True).render(f"MONEDAS {self.game.progress.data.get('coins', 0)}", True, GOLD)
        surface.blit(coins, (960, 68))
        draw_footer(surface, "Selecciona una mision desbloqueada para continuar la historia")
