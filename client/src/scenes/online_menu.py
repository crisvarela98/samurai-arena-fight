import json
from pathlib import Path

import pygame

from src.core.base_scene import BaseScene
from src.core.constants import BLUE, GOLD, GREEN, LIGHT, RED
from src.ui.button import Button
from src.ui.menu_theme import draw_backdrop, draw_chip, draw_footer, draw_panel, draw_selection_frame, draw_stage_label, get_font
from src.ui.text_input import TextInput


class OnlineMenuScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        root = Path(__file__).resolve().parents[2]
        fighters = json.loads((root / "data" / "fighters.json").read_text(encoding="utf-8"))
        arenas = json.loads((root / "data" / "arenas.json").read_text(encoding="utf-8"))
        self.fighter_names = {fighter["id"]: fighter["name"] for fighter in fighters}
        self.arena_names = {arena["id"]: arena["name"] for arena in arenas}
        self.background = self.game.assets.load_image(
            "assets/ui/menu_online_bg.png",
            size=(self.game.settings["screen_width"], self.game.settings["screen_height"]),
        )

        self.input_server = TextInput((92, 220, 470, 46), "IP O URL DEL SERVIDOR")
        self.input_username = TextInput((92, 306, 470, 46), "NOMBRE DE JUGADOR")
        self.input_room = TextInput((92, 392, 260, 46), "CODIGO DE SALA")
        self.create_button = Button((92, 480, 220, 56), "CREAR SALA", variant="primary", font_size=24)
        self.join_button = Button((330, 480, 232, 56), "UNIRSE A SALA", variant="primary", font_size=24)
        self.test_button = Button((582, 220, 150, 46), "PROBAR", font_size=20)
        self.refresh_button = Button((582, 306, 150, 46), "RECARGAR", font_size=20)
        self.back_button = Button((42, 42, 140, 46), "VOLVER", variant="ghost", font_size=20)

        self.net = self.game.network
        self.rooms = []
        self.room_rects = []
        self.status_message = "Configura tu conexion y crea una sala."
        self.status_color = LIGHT
        self.body_font = get_font("body", 20)
        self.small_font = get_font("tiny", 17)
        self.label_font = get_font("heading", 21, bold=True)

    def on_enter(self):
        self.net = self.game.network
        self._bind_network_callbacks()
        self.input_server.text = self.net.server_url
        self.input_username.text = self.game.shared.get("online_username", self.game.settings.get("username", "player"))
        self.input_room.text = self.game.shared.get("online_room") or ""
        self.game.shared["online_open_lobby"] = False
        self._refresh_rooms(silent=True)

    def _bind_network_callbacks(self):
        self.net.on("room_created", self._on_room_created)
        self.net.on("room_joined", self._on_room_joined)
        self.net.on("waiting_for_player", self._on_waiting_for_player)
        self.net.on("match_started", self._on_match_started)
        self.net.on("error_message", self._on_error)
        self.net.on("connect_error", self._on_error)
        self.net.on("opponent_left", self._on_opponent_left)

    def _set_status(self, message, color=LIGHT):
        self.status_message = message
        self.status_color = color

    def _selected_fighter_name(self):
        return self.fighter_names.get(self.game.shared["selected_fighter"], self.game.shared["selected_fighter"])

    def _selected_arena_name(self):
        return self.arena_names.get(self.game.shared["selected_arena"], self.game.shared["selected_arena"])

    def _apply_profile(self):
        username = self.input_username.text.strip() or "player"
        self.game.shared["online_username"] = username
        self.net.set_server_url(self.input_server.text.strip())
        self.game.save_settings()
        return username

    def _refresh_rooms(self, silent=False):
        try:
            self._apply_profile()
            rooms = self.net.fetch_rooms()
            self.rooms = [room for room in rooms if room.get("status") == "waiting"][:6]
            if not silent:
                if self.rooms:
                    self._set_status("Salas actualizadas. Puedes tocar una para copiar el codigo.", GREEN)
                else:
                    self._set_status("No hay salas esperando rival en este momento.", GOLD)
        except Exception as exc:
            self.rooms = []
            if not silent:
                self._set_status(f"No pude consultar salas: {exc}", RED)

    def _probe_server(self):
        try:
            self._apply_profile()
            self.net.probe_server()
            self._set_status(f"Servidor activo en {self.net.server_url}", GREEN)
            self._refresh_rooms(silent=True)
        except Exception as exc:
            self._set_status(f"No pude conectar con {self.input_server.text.strip() or 'el servidor'}: {exc}", RED)

    def _create_room(self):
        username = self._apply_profile()
        try:
            self.net.connect()
            self.net.create_room(
                username=username,
                platform=self.game.shared["selected_platform"],
                fighter_id=self.game.shared["selected_fighter"],
                arena_id=self.game.shared["selected_arena"],
            )
            self.game.shared["online_role"] = "host"
            self.game.shared["online_match_started"] = False
            self.game.shared["online_match_data"] = None
            self._set_status("Creando sala...", GOLD)
        except Exception as exc:
            self._set_status(f"No pude crear la sala: {exc}", RED)

    def _join_room(self):
        room_code = self.input_room.text.strip().upper()
        if not room_code:
            self._set_status("Ingresa o selecciona un codigo de sala.", RED)
            return
        username = self._apply_profile()
        try:
            self.net.connect()
            self.net.join_room(
                room_code=room_code,
                username=username,
                platform=self.game.shared["selected_platform"],
                fighter_id=self.game.shared["selected_fighter"],
                arena_id=self.game.shared["selected_arena"],
            )
            self.game.shared["online_role"] = "guest"
            self.game.shared["online_match_started"] = False
            self.game.shared["online_match_data"] = None
            self.game.shared["online_room"] = room_code
            self._set_status(f"Uniendome a {room_code}...", GOLD)
        except Exception as exc:
            self._set_status(f"No pude unirme a la sala: {exc}", RED)

    def _on_room_created(self, data):
        self.game.shared["online_room"] = data.get("roomCode")
        self.game.shared["online_match_started"] = False
        self.game.shared["online_match_data"] = data
        self.game.shared["online_open_lobby"] = True
        self._set_status(f"Sala {data.get('roomCode')} creada. Comparte IP y codigo con el otro jugador.", GREEN)

    def _on_room_joined(self, data):
        self.game.shared["online_room"] = data.get("roomCode")
        self.game.shared["online_match_started"] = False
        self.game.shared["online_match_data"] = data
        self.game.shared["online_open_lobby"] = True
        self._set_status(f"Entraste a la sala {data.get('roomCode')}. Esperando que la pelea arranque.", GREEN)

    def _on_waiting_for_player(self, data):
        self.game.shared["online_room"] = data.get("roomCode")
        self._set_status(f"Sala {data.get('roomCode')} lista. Falta un solo jugador.", GOLD)

    def _on_match_started(self, data):
        self.game.shared["online_match_started"] = True
        self.game.shared["online_room"] = data.get("roomCode")
        self.game.shared["online_match_data"] = data
        self.game.shared["selected_arena"] = data.get("arenaId", self.game.shared["selected_arena"])

    def _on_error(self, data):
        self._set_status(data.get("message", "Error online desconocido"), RED)

    def _on_opponent_left(self, data):
        self._set_status(data.get("message", "El rival salio de la sala"), RED)

    def update(self, dt):
        if self.game.shared.get("online_open_lobby"):
            self.game.shared["online_open_lobby"] = False
            self.game.go("lobby")

    def handle_event(self, event):
        self.input_server.handle_event(event)
        self.input_username.handle_event(event)
        self.input_room.handle_event(event)

        if event.type == pygame.MOUSEBUTTONUP:
            if self.handle_music_toggle_event(event):
                return
            if self.back_button.rect.collidepoint(event.pos):
                self.game.go("arena")
                return
            if self.test_button.rect.collidepoint(event.pos):
                self._probe_server()
                return
            if self.refresh_button.rect.collidepoint(event.pos):
                self._refresh_rooms()
                return
            if self.create_button.rect.collidepoint(event.pos):
                self._create_room()
                return
            if self.join_button.rect.collidepoint(event.pos):
                self._join_room()
                return
            for room, rect in self.room_rects:
                if rect.collidepoint(event.pos):
                    self.input_room.text = room.get("roomCode", "")
                    self._set_status(f"Sala {room.get('roomCode', '')} seleccionada.", BLUE)
                    return

    def draw(self, surface):
        draw_backdrop(surface, self.background, overlay_color=(6, 7, 10, 128))
        self.back_button.draw(surface)
        self.draw_music_toggle(surface)
        draw_stage_label(surface, "ONLINE", "Crea o entra a una sala desde Android con la misma IP/URL y codigo.", x=206, y=54)

        setup_panel = pygame.Rect(48, 118, 706, 548)
        rooms_panel = pygame.Rect(782, 118, 450, 548)
        draw_panel(surface, setup_panel, title="CONFIGURACION DE PARTIDA")
        draw_panel(surface, rooms_panel, title="SALAS ABIERTAS")

        surface.blit(self.label_font.render("SERVIDOR", True, LIGHT), (92, 190))
        surface.blit(self.label_font.render("JUGADOR", True, LIGHT), (92, 276))
        surface.blit(self.label_font.render("SALA", True, LIGHT), (92, 362))
        self.input_server.draw(surface)
        self.input_username.draw(surface)
        self.input_room.draw(surface)
        self.test_button.draw(surface)
        self.refresh_button.draw(surface)
        self.create_button.draw(surface)
        self.join_button.draw(surface)

        draw_chip(surface, pygame.Rect(92, 564, 150, 30), "ANDROID")
        draw_chip(surface, pygame.Rect(252, 564, 168, 30), self._selected_fighter_name().upper())
        draw_chip(surface, pygame.Rect(430, 564, 214, 30), self._selected_arena_name().upper(), accent=(80, 180, 95))

        tips = [
            "1. Crea la sala desde el dispositivo principal.",
            "2. Usa la misma red WiFi o la misma IP configurada.",
            "3. Comparte el codigo de sala y entra desde Android.",
        ]
        for index, line in enumerate(tips):
            surface.blit(self.small_font.render(line, True, LIGHT), (92, 612 + index * 20))

        self.room_rects = []
        if not self.rooms:
            empty = get_font("body", 22).render("No hay salas esperando rival.", True, LIGHT)
            surface.blit(empty, (852, 214))
        else:
            for index, room in enumerate(self.rooms):
                rect = pygame.Rect(810, 190 + index * 70, 392, 56)
                self.room_rects.append((room, rect))
                draw_selection_frame(surface, rect, selected=self.input_room.text.strip().upper() == room.get("roomCode", ""))
                code = get_font("heading", 22, bold=True).render(room.get("roomCode", "------"), True, GOLD)
                players = ", ".join(room.get("players", [])) or "sin jugadores"
                surface.blit(code, (rect.x + 18, rect.y + 10))
                surface.blit(self.small_font.render(players, True, LIGHT), (rect.x + 18, rect.y + 32))

        status_box = pygame.Rect(810, 610, 392, 38)
        pygame.draw.rect(surface, (10, 12, 16), status_box, border_radius=12)
        pygame.draw.rect(surface, self.status_color, status_box, 2, border_radius=12)
        status = self.small_font.render(self.status_message, True, self.status_color)
        surface.blit(status, (status_box.x + 14, status_box.y + 10))

        draw_footer(surface, "Consejo: usa la misma red y el mismo codigo de sala")
