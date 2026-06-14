import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GOLD, GREEN, LIGHT, RED
from src.ui.button import Button
from src.ui.health_bar import draw_portrait_badge
from src.ui.menu_theme import draw_backdrop, draw_chip, draw_footer, draw_panel, get_font
from src.utils.online_fighter_factory import get_online_clan_preset


class LobbyScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.net = None
        self.background = self.game.assets.load_image(
            "assets/ui/menu_online_bg.png",
            size=(self.game.settings["screen_width"], self.game.settings["screen_height"]),
        )
        self.font = get_font("heading", 34, bold=True)
        self.small = get_font("body", 22)
        self.tiny = get_font("tiny", 18)
        self.code_font = get_font("display", 54, bold=True)
        self.leave_button = Button((540, 592, 200, 52), "SALIR", variant="danger", font_size=22)

    def on_enter(self):
        self.net = self.game.network

    def _leave_lobby(self):
        if self.net:
            try:
                self.net.leave_room()
            except Exception:
                pass
        self.game.shared["online_room"] = None
        self.game.shared["online_match_started"] = False
        self.game.shared["online_match_data"] = None
        self.game.go("menu")

    def _portrait_for_profile(self, profile):
        portrait_path = profile.get("portrait")
        if not portrait_path:
            preset = get_online_clan_preset(
                self.game.client_dir,
                profile.get("clan_id") or profile.get("clanId", "cuervo_negro"),
            )
            portrait_path = preset.get("portrait", "")
        return self.game.assets.load_image(portrait_path, trim_alpha=True) if portrait_path else None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._leave_lobby()
        if event.type == pygame.MOUSEBUTTONUP:
            if self.handle_music_toggle_event(event):
                return
            if self.leave_button.rect.collidepoint(event.pos):
                self._leave_lobby()

    def update(self, dt):
        if self.game.shared.get("online_match_started"):
            self.game.shared["online_match_started"] = False
            self.game.go("online_battle")

    def draw(self, surface):
        draw_backdrop(surface, self.background, overlay_color=(8, 8, 10, 150))
        self.draw_music_toggle(surface)
        panel = pygame.Rect(146, 96, 988, 548)
        draw_panel(surface, panel, title="SALA ONLINE")

        room_code = self.game.shared.get("online_room") or (self.net.state.room_code if self.net else "...")
        role = (self.game.shared.get("online_role") or "-").upper()
        username = self.game.shared.get("online_username", "player")
        arena = self.game.shared.get("selected_arena", "coliseo_de_acero").replace("_", " ").title()
        online_fighter = self.game.shared.get("online_fighter") or {}
        fighter = online_fighter.get("fighter_name", online_fighter.get("clan_name", "Guerrero online"))
        portrait = self._portrait_for_profile(online_fighter)
        status_text = "Conectado" if self.net and self.net.state.connected else "Sin conexion"
        status_color = GREEN if self.net and self.net.state.connected else RED

        title = self.font.render("PREPARANDO ENFRENTAMIENTO", True, LIGHT)
        surface.blit(title, title.get_rect(center=(640, 152)))
        surface.blit(self.code_font.render(room_code, True, GOLD), (208, 202))
        surface.blit(self.small.render("Comparte este codigo con el segundo jugador.", True, LIGHT), (212, 270))

        if portrait is not None:
            badge_rect = pygame.Rect(500, 186, 214, 318)
            portrait_shadow = portrait.copy()
            portrait_shadow.set_alpha(156)
            draw_portrait_badge(surface, badge_rect, portrait_shadow, accent=(196, 160, 78))

        draw_chip(surface, pygame.Rect(210, 318, 136, 32), f"ROL {role}")
        draw_chip(surface, pygame.Rect(358, 318, 160, 32), "ANDROID", accent=(80, 180, 95))
        draw_chip(surface, pygame.Rect(530, 318, 250, 32), fighter.upper(), accent=(80, 180, 95))

        left_lines = [
            f"Jugador: {username}",
            f"Arma: {online_fighter.get('weapon_name', 'Katana')}",
            f"Arena: {arena}",
            f"Servidor: {(self.net.server_url if self.net else '-').replace('http://', '').replace('https://', '')}",
            f"Estado de red: {status_text}",
        ]
        for index, line in enumerate(left_lines):
            color = status_color if line.startswith("Estado") else LIGHT
            surface.blit(self.small.render(line, True, color), (212, 384 + index * 34))

        match_data = self.game.shared.get("online_match_data") or {}
        players = match_data.get("players") or []
        draw_panel(surface, pygame.Rect(742, 202, 332, 286), title="JUGADORES")
        if players:
            for index, player in enumerate(players[:2]):
                y = 244 + index * 98
                player_portrait = self._portrait_for_profile(player)
                draw_portrait_badge(surface, pygame.Rect(768, y, 74, 98), player_portrait, accent=(80, 180, 95))
                draw_chip(surface, pygame.Rect(856, y + 12, 112, 28), "LISTO", accent=(80, 180, 95))
                name = self.small.render(player.get("username", "player").upper(), True, GOLD)
                fighter_line = self.tiny.render(
                    f"{player.get('clanName', 'Clan')} / {player.get('weaponName', 'Arma')}", True, LIGHT
                )
                surface.blit(name, (856, y + 46))
                surface.blit(fighter_line, (856, y + 74))
        else:
            wait = self.small.render("Esperando al segundo jugador...", True, GOLD)
            surface.blit(wait, (770, 278))

        surface.blit(self.tiny.render("Cuando la sala tenga dos jugadores, la pelea inicia sola.", True, GOLD), (212, 532))
        surface.blit(self.tiny.render("Si algo falla, ambos clientes deben apuntar a la misma URL/IP.", True, GOLD), (212, 558))
        self.leave_button.draw(surface)
        draw_footer(surface, "Lobby listo para iniciar la pelea")
