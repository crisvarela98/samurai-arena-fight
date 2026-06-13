import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GOLD, GREEN, LIGHT
from src.ui.button import Button
from src.ui.menu_theme import draw_backdrop, draw_chip, draw_panel, draw_selection_frame, get_font
from src.ui.text_input import TextInput
from src.utils.online_fighter_factory import build_online_fighter, load_online_catalog


class OnlineCharacterCreateScene(BaseScene):
    COLORS = [(174, 42, 48), (48, 96, 176), (202, 162, 68), (220, 220, 224)]

    def __init__(self, game):
        super().__init__(game)
        self.background = self.game.assets.load_image("assets/ui/menu_online_bg.png", size=(1280, 720))
        self.clans, self.weapons, self.fighter_config = load_online_catalog(self.game.client_dir)
        self.selected_clan = "cuervo_negro"
        self.selected_weapon = "katana"
        self.selected_color = self.COLORS[0]
        self.name_input = TextInput((92, 178, 370, 46), "NOMBRE DEL GUERRERO", max_length=24)
        self.clan_buttons = [Button((82, 284 + index * 66, 410, 52), clan["name"], font_size=18) for index, clan in enumerate(self.clans)]
        self.weapon_buttons = [Button((554 + (index % 2) * 300, 190 + (index // 2) * 74, 270, 54), weapon["name"], font_size=20) for index, weapon in enumerate(self.weapons)]
        self.continue_button = Button((924, 590, 250, 58), "CONTINUAR", variant="primary", font_size=23)
        self.back_button = Button((42, 42, 140, 46), "VOLVER", variant="ghost", font_size=20)

    def on_enter(self):
        account = self.game.shared.get("account_user") or {}
        profile = self.game.shared.get("online_fighter") or {}
        self.name_input.text = profile.get("username") or account.get("username") or self.game.auth.session.get("username", "guerrero")
        self.selected_clan = profile.get("clan_id", "cuervo_negro")
        self.selected_weapon = profile.get("weapon_id", "katana")
        self.selected_color = tuple(profile.get("color", self.COLORS[0]))

    def _continue(self):
        fighter = build_online_fighter(
            self.game.client_dir, self.name_input.text, self.selected_clan, self.selected_weapon, self.selected_color
        )
        self.game.shared["online_fighter"] = fighter
        self.game.shared["online_username"] = fighter["username"]
        self.game.shared["match_mode"] = "online"
        try:
            self.game.auth.sync_progress(self.game.progress.data, fighter)
        except Exception:
            pass
        self.game.go("arena")

    def handle_event(self, event):
        self.name_input.handle_event(event)
        if event.type != pygame.MOUSEBUTTONUP:
            return
        if self.back_button.rect.collidepoint(event.pos):
            self.game.go("menu")
            return
        if self.continue_button.rect.collidepoint(event.pos):
            self._continue()
            return
        for clan, button in zip(self.clans, self.clan_buttons):
            if button.rect.collidepoint(event.pos):
                self.selected_clan = clan["id"]
                return
        for weapon, button in zip(self.weapons, self.weapon_buttons):
            if button.rect.collidepoint(event.pos):
                self.selected_weapon = weapon["id"]
                return
        for index, color in enumerate(self.COLORS):
            if pygame.Rect(566 + index * 82, 496, 58, 58).collidepoint(event.pos):
                self.selected_color = color

    def draw(self, surface):
        draw_backdrop(surface, self.background, overlay_color=(4, 6, 10, 166))
        self.back_button.draw(surface)
        draw_panel(surface, pygame.Rect(52, 112, 458, 550), title="IDENTIDAD ONLINE")
        draw_panel(surface, pygame.Rect(530, 112, 698, 550), title="ARMA Y APARIENCIA")
        surface.blit(get_font("body", 19, bold=True).render("NOMBRE", True, LIGHT), (92, 150))
        self.name_input.draw(surface)
        surface.blit(get_font("heading", 21, bold=True).render("CLAN", True, GOLD), (82, 248))
        for clan, button in zip(self.clans, self.clan_buttons):
            button.draw(surface, selected=clan["id"] == self.selected_clan)
        for weapon, button in zip(self.weapons, self.weapon_buttons):
            button.draw(surface, selected=weapon["id"] == self.selected_weapon)
        surface.blit(get_font("heading", 21, bold=True).render("COLOR PRINCIPAL", True, GOLD), (554, 456))
        for index, color in enumerate(self.COLORS):
            rect = pygame.Rect(566 + index * 82, 496, 58, 58)
            pygame.draw.rect(surface, color, rect, border_radius=12)
            pygame.draw.rect(surface, GOLD if color == self.selected_color else LIGHT, rect, 4 if color == self.selected_color else 1, border_radius=12)
        clan = next(item for item in self.clans if item["id"] == self.selected_clan)
        weapon = next(item for item in self.weapons if item["id"] == self.selected_weapon)
        draw_chip(surface, pygame.Rect(554, 574, 330, 30), clan["style"].upper(), accent=GREEN)
        description = get_font("tiny", 17).render(weapon["description"], True, LIGHT)
        surface.blit(description, (554, 620))
        self.continue_button.draw(surface, selected=True)
