import json
from pathlib import Path

import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GOLD, LIGHT, RED
from src.ui.button import Button
from src.ui.menu_theme import draw_backdrop, draw_panel, get_font


class MemoryFragmentScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        root = Path(__file__).resolve().parents[2]
        fragments = json.loads((root / "data" / "story" / "memory_fragments.json").read_text(encoding="utf-8"))
        self.fragments = {item["id"]: item for item in fragments}
        self.background = self.game.assets.load_image("assets/fighters/portraits/kenji_portrait.png", trim_alpha=True)
        self.continue_button = Button((526, 578, 228, 52), "DESPERTAR", variant="primary", font_size=22)
        self.timer = 0.0

    def on_enter(self):
        self.timer = 0.0

    def _finish(self):
        next_scene = self.game.shared.get("memory_next_scene", "story_map")
        if next_scene == "menu":
            self.game.shared["story_episode_active"] = False
        self.game.go(next_scene)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP and self.continue_button.rect.collidepoint(event.pos):
            self._finish()

    def update(self, dt):
        self.timer += dt
        if self.game.shared.get("story_episode_active"):
            elapsed = self.game.shared.get("story_episode_elapsed", 0.0) + dt
            self.game.shared["story_episode_elapsed"] = elapsed
            remaining = max(0.0, 120.0 - elapsed)
            if self.timer >= min(5.0, max(0.2, remaining)):
                self._finish()

    @staticmethod
    def _wrap_text(text, font, max_width):
        lines = []
        current = []
        for word in text.split():
            candidate = " ".join((*current, word))
            if current and font.size(candidate)[0] > max_width:
                lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(" ".join(current))
        return lines

    def draw(self, surface):
        surface.fill((2, 2, 4))
        ghost = pygame.transform.smoothscale(self.background, (520, 650))
        ghost.set_alpha(96)
        surface.blit(ghost, ghost.get_rect(center=(640, 356)))
        red_flash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        red_flash.fill((110, 0, 0, 42))
        surface.blit(red_flash, (0, 0))
        fragment = self.fragments.get(self.game.shared.get("memory_fragment_id"), {"title": "Recuerdo perdido", "text": "Nada permanece."})
        draw_panel(surface, pygame.Rect(180, 154, 920, 404), title="FRAGMENTO DE MEMORIA")
        title = get_font("display", 50, bold=True).render(fragment["title"].upper(), True, RED)
        body_font = get_font("body", 26)
        warning = get_font("tiny", 18, bold=True).render("NO TODOS LOS RECUERDOS DICEN LA VERDAD", True, GOLD)
        surface.blit(title, title.get_rect(center=(640, 280)))
        lines = self._wrap_text(fragment["text"], body_font, 760)
        line_height = body_font.get_linesize() + 4
        start_y = 378 - ((len(lines) - 1) * line_height) // 2
        for index, line in enumerate(lines):
            text = body_font.render(line, True, LIGHT)
            surface.blit(text, text.get_rect(center=(640, start_y + index * line_height)))
        surface.blit(warning, warning.get_rect(center=(640, 448)))
        self.continue_button.draw(surface, selected=True)
