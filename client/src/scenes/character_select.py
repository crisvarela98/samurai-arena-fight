import json
from pathlib import Path

import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GOLD, GREEN, LIGHT, RED
from src.ui.button import Button
from src.ui.menu_theme import (
    blit_contain,
    draw_backdrop,
    draw_chip,
    draw_footer,
    draw_panel,
    draw_selection_frame,
    draw_stage_label,
    draw_stat_bar,
    get_font,
)


class CharacterSelectScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        root = Path(__file__).resolve().parents[2]
        self.background = self.game.assets.load_image(
            "assets/ui/menu_armory_bg.png",
            size=(self.game.settings["screen_width"], self.game.settings["screen_height"]),
        )
        self.fighters = json.loads((root / "data" / "fighters.json").read_text(encoding="utf-8"))
        weapons = json.loads((root / "data" / "weapons.json").read_text(encoding="utf-8"))
        self.weapon_map = {weapon["id"]: weapon for weapon in weapons}

        self.cards = []
        self.preview_frames = {}
        self.hero_portraits = {}
        card_positions = [pygame.Rect(620, 170, 560, 190), pygame.Rect(620, 390, 560, 190)]
        for fighter, rect in zip(self.fighters, card_positions):
            self.cards.append((fighter, Button(rect, fighter["name"], font_size=26, variant="ghost")))
            self.preview_frames[fighter["id"]] = self.game.assets.load_sprite_strip(
                fighter["sprite_sheet"],
                7,
                scale_height=140,
                chroma_key=(0, 255, 0),
                chroma_tolerance=92,
                despill=True,
            )[0]
            portrait_path = fighter.get("portrait")
            self.hero_portraits[fighter["id"]] = (
                self.game.assets.load_image(portrait_path, trim_alpha=True) if portrait_path else None
            )

        self.next_button = Button((1010, 618, 170, 52), "SIGUIENTE", variant="primary", font_size=24)
        self.back_button = Button((42, 42, 140, 46), "VOLVER", variant="ghost", font_size=20)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            if self.handle_music_toggle_event(event):
                return
            if self.back_button.rect.collidepoint(event.pos):
                self.game.go("menu")
                return
            for fighter, button in self.cards:
                if button.rect.collidepoint(event.pos):
                    self.game.shared["selected_fighter"] = fighter["id"]
            if self.next_button.rect.collidepoint(event.pos):
                self.game.go("arena")

    def draw(self, surface):
        draw_backdrop(surface, self.background, overlay_color=(8, 7, 10, 138))
        self.back_button.draw(surface)
        self.draw_music_toggle(surface)
        draw_stage_label(surface, "ELIGE TU GUERRERO", "Cada combatiente cambia ritmo, daño y resistencia.", x=206, y=54)

        showcase_rect = pygame.Rect(54, 120, 500, 542)
        list_rect = pygame.Rect(592, 120, 636, 542)
        draw_panel(surface, showcase_rect, title="PERFIL DEL GUERRERO")
        draw_panel(surface, list_rect, title="ROSTER")

        selected = next(fighter for fighter in self.fighters if fighter["id"] == self.game.shared["selected_fighter"])
        weapon = self.weapon_map[selected["weapon_id"]]
        portrait = self.hero_portraits[selected["id"]]

        draw_chip(surface, pygame.Rect(92, 194, 136, 30), selected["weapon_id"].upper())
        draw_chip(surface, pygame.Rect(236, 194, 160, 30), f"DEF {selected['defense']}", accent=(80, 180, 95))

        art_rect = pygame.Rect(76, 170, 398, 286)
        glow = pygame.Surface((art_rect.width + 40, art_rect.height + 40), pygame.SRCALPHA)
        pygame.draw.circle(glow, (196, 160, 78, 72), (glow.get_width() // 2, glow.get_height() // 2), 124)
        pygame.draw.circle(glow, (255, 255, 255, 18), (glow.get_width() // 2 - 18, glow.get_height() // 2 - 26), 96)
        surface.blit(glow, (art_rect.x - 20, art_rect.y - 12))

        if portrait is not None:
            blit_contain(surface, portrait, art_rect, bottom_align=True)
        else:
            hero_frame = self.preview_frames[selected["id"]]
            hero_rect = hero_frame.get_rect(center=(304, 334))
            surface.blit(hero_frame, hero_rect)

        title = get_font("display", 46, bold=True).render(selected["name"].upper(), True, GOLD)
        surface.blit(title, (88, 470))
        weapon_text = get_font("body", 20).render(f"Arma: {weapon['name']}  |  Cooldown: {weapon['cooldown']:.2f}s", True, LIGHT)
        surface.blit(weapon_text, (88, 516))
        draw_stat_bar(surface, pygame.Rect(88, 560, 170, 16), "VIDA", selected["max_health"], 160, RED)
        draw_stat_bar(surface, pygame.Rect(280, 560, 170, 16), "STAMINA", selected["max_stamina"], 120, GOLD)
        draw_stat_bar(surface, pygame.Rect(88, 604, 170, 16), "VELOCIDAD", selected["speed"], 260, (86, 150, 230))
        draw_stat_bar(surface, pygame.Rect(280, 604, 170, 16), "ATAQUE", selected["attack_power"], 30, GREEN)

        for fighter, button in self.cards:
            rect = button.rect
            active = fighter["id"] == selected["id"]
            draw_selection_frame(surface, rect, selected=active)
            preview = self.preview_frames[fighter["id"]]
            preview_rect = preview.get_rect(center=(rect.x + 98, rect.centery + 8))
            surface.blit(preview, preview_rect)
            name = get_font("heading", 28, bold=True).render(fighter["name"].upper(), True, GOLD if active else LIGHT)
            surface.blit(name, (rect.x + 170, rect.y + 26))
            weapon_name = self.weapon_map[fighter["weapon_id"]]["name"]
            meta = get_font("body", 18).render(f"{weapon_name}  |  Vida {fighter['max_health']}  |  Ataque {fighter['attack_power']}", True, LIGHT)
            surface.blit(meta, (rect.x + 170, rect.y + 66))
            desc = get_font("tiny", 16).render(
                "Seleccionado" if active else "Presiona para elegir este guerrero",
                True,
                GREEN if active else LIGHT,
            )
            surface.blit(desc, (rect.x + 170, rect.y + 104))
            if active:
                draw_chip(surface, pygame.Rect(rect.right - 144, rect.y + 24, 116, 28), "ACTIVO", accent=(80, 180, 95))

        self.next_button.draw(surface, selected=True)
        draw_footer(surface, "Revisa stats y elige el samurai que mejor combine con tu estilo")
