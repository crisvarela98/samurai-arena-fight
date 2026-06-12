import json
from pathlib import Path

import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GOLD, LIGHT
from src.ui.button import Button
from src.ui.menu_theme import draw_backdrop, draw_chip, draw_footer, draw_panel, draw_selection_frame, draw_stage_label, get_font


def _wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines


class ArenaSelectScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        root = Path(__file__).resolve().parents[2]
        self.background = self.game.assets.load_image(
            "assets/ui/menu_main_bg.png",
            size=(self.game.settings["screen_width"], self.game.settings["screen_height"]),
        )
        self.arenas = json.loads((root / "data" / "arenas.json").read_text(encoding="utf-8"))
        self.descriptions = {
            "coliseo_de_acero": "Una fortaleza industrial iluminada por hornos, cadenas y metal al rojo vivo.",
            "templo_en_llamas": "Un santuario devorado por el fuego, luna llena y brasas en el aire.",
        }
        self.cards = []
        self.thumbnails = {}
        card_positions = [pygame.Rect(70, 196, 540, 292), pygame.Rect(670, 196, 540, 292)]
        for arena, rect in zip(self.arenas, card_positions):
            self.cards.append((arena, Button(rect, arena["name"], font_size=28, variant="ghost")))
            self.thumbnails[arena["id"]] = self.game.assets.load_image(arena["background"], size=(rect.width - 20, 180))
        self.next_button = Button((1010, 612, 180, 54), "SIGUIENTE", variant="primary", font_size=24)
        self.back_button = Button((42, 42, 140, 46), "VOLVER", variant="ghost", font_size=20)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            if self.handle_music_toggle_event(event):
                return
            if self.back_button.rect.collidepoint(event.pos):
                self.game.go("character")
                return
            for arena, button in self.cards:
                if button.rect.collidepoint(event.pos):
                    self.game.shared["selected_arena"] = arena["id"]
            if self.next_button.rect.collidepoint(event.pos):
                if self.game.shared.get("match_mode") == "online":
                    self.game.go("online_menu")
                else:
                    self.game.go("battle")

    def draw(self, surface):
        draw_backdrop(surface, self.background, overlay_color=(6, 7, 10, 150))
        self.back_button.draw(surface)
        self.draw_music_toggle(surface)
        draw_stage_label(surface, "ELIGE TU ARENA", "Cada escenario define la atmosfera del duelo.", x=206, y=54)

        draw_panel(surface, pygame.Rect(40, 120, 1200, 556), title="ESCENARIOS DISPONIBLES")

        for arena, button in self.cards:
            rect = button.rect
            active = self.game.shared["selected_arena"] == arena["id"]
            draw_selection_frame(surface, rect, selected=active)
            thumb = self.thumbnails[arena["id"]]
            thumb_rect = pygame.Rect(rect.x + 10, rect.y + 10, rect.width - 20, 180)
            surface.blit(thumb, thumb_rect)
            gradient = pygame.Surface((thumb_rect.width, thumb_rect.height), pygame.SRCALPHA)
            gradient.fill((0, 0, 0, 0))
            pygame.draw.rect(gradient, (0, 0, 0, 80), gradient.get_rect(), border_radius=14)
            surface.blit(gradient, thumb_rect.topleft)

            name = get_font("heading", 28, bold=True).render(arena["name"].upper(), True, GOLD if active else LIGHT)
            surface.blit(name, (rect.x + 20, rect.y + 206))
            body_font = get_font("body", 18)
            wrapped_description = _wrap_text(self.descriptions.get(arena["id"], arena["name"]), body_font, rect.width - 40)
            for line_index, line in enumerate(wrapped_description[:2]):
                description = body_font.render(line, True, LIGHT)
                surface.blit(description, (rect.x + 20, rect.y + 244 + line_index * 22))
            draw_chip(surface, pygame.Rect(rect.x + 20, rect.y + 24, 108, 28), "ACTIVA" if active else "ARENA")
            floor_text = get_font("tiny", 16, bold=True).render(f"Piso {arena['floor_y']}", True, LIGHT)
            surface.blit(floor_text, (rect.right - 110, rect.y + 24))

        selected_name = next(arena["name"] for arena in self.arenas if arena["id"] == self.game.shared["selected_arena"])
        info = get_font("body", 20).render(f"Arena seleccionada: {selected_name}", True, LIGHT)
        surface.blit(info, (74, 618))
        self.next_button.draw(surface, selected=True)
        draw_footer(surface, "Tip: cada arena mantiene el mismo plano de combate pero cambia la lectura visual")
