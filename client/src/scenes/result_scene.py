import json
from pathlib import Path

import pygame

from src.core.base_scene import BaseScene
from src.ui.button import Button
from src.ui.menu_theme import blit_contain, draw_backdrop, draw_footer, draw_panel, get_font, tone_for_result


class ResultScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.background = self.game.assets.load_image(
            "assets/ui/menu_main_bg.png",
            size=(self.game.settings["screen_width"], self.game.settings["screen_height"]),
        )
        root = Path(__file__).resolve().parents[2]
        fighters = json.loads((root / "data" / "fighters.json").read_text(encoding="utf-8"))
        self.portraits = {
            fighter["id"]: self.game.assets.load_image(fighter["portrait"], trim_alpha=True)
            for fighter in fighters
            if fighter.get("portrait")
        }
        self.button = Button((540, 516, 200, 52), "CONTINUAR", variant="primary", font_size=24)
        self.title_font = get_font("display", 76, bold=True)
        self.body_font = get_font("body", 22)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            if self.handle_music_toggle_event(event):
                return
            if self.button.rect.collidepoint(event.pos):
                self.game.shared["online_room"] = None
                self.game.shared["online_match_data"] = None
                self.game.shared["online_match_started"] = False
                self.game.shared["online_battle_exit"] = False
                self.game.shared["result_detail"] = None
                self.game.go("menu")

    def draw(self, surface):
        draw_backdrop(surface, self.background, overlay_color=(6, 8, 12, 172))
        self.draw_music_toggle(surface)
        panel = pygame.Rect(248, 116, 784, 456)
        draw_panel(surface, panel, title="RESULTADO DEL COMBATE")

        result = self.game.shared.get("result") or "resultado"
        title = result.replace("_", " ").upper()
        color = tone_for_result(result)
        portrait = self.portraits.get(self.game.shared.get("selected_fighter", "kenji"))

        if portrait is not None:
            art_rect = pygame.Rect(290, 182, 240, 322)
            glow = pygame.Surface((art_rect.width + 40, art_rect.height + 40), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 62), (glow.get_width() // 2, glow.get_height() // 2), 120)
            surface.blit(glow, (art_rect.x - 20, art_rect.y - 8))
            blit_contain(surface, portrait, art_rect, bottom_align=True)

        text = self.title_font.render(title, True, color)
        surface.blit(text, text.get_rect(center=(772, 276)))

        descriptions = {
            "victory": "Tu espada dominó la arena. Continúa hacia el siguiente duelo.",
            "defeat": "El combate se perdió. Ajusta estrategia y vuelve a intentarlo.",
        }
        message = descriptions.get(result, str(result))
        body = self.body_font.render(message, True, (235, 230, 220))
        surface.blit(body, body.get_rect(center=(790, 368)))
        detail = self.game.shared.get("result_detail")
        if detail:
            detail_text = self.body_font.render(str(detail).upper(), True, color)
            surface.blit(detail_text, detail_text.get_rect(center=(790, 408)))
        self.button.draw(surface, selected=True)
        draw_footer(surface, "La arena siempre recompensa a quien aprende del ultimo duelo")
