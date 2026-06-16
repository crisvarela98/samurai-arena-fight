from dataclasses import dataclass
from urllib.parse import urlparse

import requests

try:
    import socketio
except Exception:  # pragma: no cover
    socketio = None


@dataclass
class NetworkState:
    connected: bool = False
    room_code: str | None = None
    role: str | None = None
    opponent: dict | None = None
    last_error: str | None = None
    socket_id: str | None = None


class NetworkClient:
    def __init__(self, server_url, auth_token=None):
        self.server_url = self.normalize_server_url(server_url)
        self.auth_token = auth_token
        self.state = NetworkState()
        self.sio = None
        self.callbacks = {}
        if socketio:
            self.sio = socketio.Client(reconnection=True, logger=False, engineio_logger=False)
            self._bind_events()

    @staticmethod
    def normalize_server_url(server_url):
        raw_value = str(server_url or "").strip()
        if not raw_value:
            return "http://localhost:3000"
        if raw_value.startswith("ws://"):
            raw_value = "http://" + raw_value[5:]
        elif raw_value.startswith("wss://"):
            raw_value = "https://" + raw_value[6:]
        elif "://" not in raw_value:
            raw_value = f"http://{raw_value}"

        parsed = urlparse(raw_value)
        scheme = parsed.scheme or "http"
        netloc = parsed.netloc or parsed.path
        path = parsed.path if parsed.netloc else ""
        normalized = f"{scheme}://{netloc}{path}".rstrip("/")
        return normalized

    def _bind_events(self):
        @self.sio.event
        def connect():
            self.state.connected = True
            self.state.socket_id = self.sio.get_sid("/")

        @self.sio.event
        def disconnect():
            self.state.connected = False
            self.state.socket_id = None

        @self.sio.event
        def connect_error(data):
            message = data if isinstance(data, str) else "No se pudo conectar al servidor"
            self.state.last_error = message
            self._emit_callback("connect_error", {"message": message})

        @self.sio.on("room_created")
        def room_created(data):
            self.state.room_code = data.get("roomCode")
            self.state.role = "host"
            self._emit_callback("room_created", data)

        @self.sio.on("room_joined")
        def room_joined(data):
            self.state.room_code = data.get("roomCode")
            self.state.role = "guest"
            self._emit_callback("room_joined", data)

        @self.sio.on("waiting_for_player")
        def waiting_for_player(data):
            self._emit_callback("waiting_for_player", data)

        @self.sio.on("match_started")
        def match_started(data):
            self._emit_callback("match_started", data)

        @self.sio.on("opponent_input")
        def opponent_input(data):
            self._emit_callback("opponent_input", data)

        @self.sio.on("opponent_attack")
        def opponent_attack(data):
            self._emit_callback("opponent_attack", data)

        @self.sio.on("opponent_block")
        def opponent_block(data):
            self._emit_callback("opponent_block", data)

        @self.sio.on("opponent_dodge")
        def opponent_dodge(data):
            self._emit_callback("opponent_dodge", data)

        @self.sio.on("fighter_hit")
        def fighter_hit(data):
            self._emit_callback("fighter_hit", data)

        @self.sio.on("health_update")
        def health_update(data):
            self._emit_callback("health_update", data)

        @self.sio.on("round_finished")
        def round_finished(data):
            self._emit_callback("round_finished", data)

        @self.sio.on("round_started")
        def round_started(data):
            self._emit_callback("round_started", data)

        @self.sio.on("match_finished")
        def match_finished(data):
            self._emit_callback("match_finished", data)

        @self.sio.on("opponent_left")
        def opponent_left(data):
            self._emit_callback("opponent_left", data)

        @self.sio.on("error_message")
        def error_message(data):
            self.state.last_error = data.get("message")
            self._emit_callback("error_message", data)

    def on(self, event, callback):
        self.callbacks[event] = callback

    def _emit_callback(self, event, data):
        callback = self.callbacks.get(event)
        if callback:
            callback(data)

    def set_server_url(self, server_url):
        normalized = self.normalize_server_url(server_url)
        if normalized == self.server_url:
            return normalized
        was_connected = bool(self.sio and self.sio.connected)
        if was_connected:
            self.disconnect()
        self.server_url = normalized
        self.state.last_error = None
        self.state.room_code = None
        self.state.role = None
        return normalized

    def set_auth_token(self, token):
        if token == self.auth_token:
            return
        if self.sio and self.sio.connected:
            self.disconnect()
        self.auth_token = token

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}

    def rest_url(self, path):
        return f"{self.server_url.rstrip('/')}/{path.lstrip('/')}"

    def probe_server(self, timeout=2.0):
        response = requests.get(self.rest_url("/health"), timeout=timeout)
        response.raise_for_status()
        return response.json()

    def fetch_rooms(self, timeout=3.0):
        response = requests.get(self.rest_url("/api/rooms"), headers=self._auth_headers(), timeout=timeout)
        response.raise_for_status()
        return response.json()

    def fetch_ranking(self, timeout=3.0, range_name="global", tz_offset_minutes=None):
        params = {"range": range_name}
        if tz_offset_minutes is not None:
            params["tzOffsetMinutes"] = int(tz_offset_minutes)
        response = requests.get(self.rest_url("/api/ranking"), headers=self._auth_headers(), params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()

    def fetch_clan_ranking(self, timeout=3.0, range_name="global", tz_offset_minutes=None):
        params = {"range": range_name}
        if tz_offset_minutes is not None:
            params["tzOffsetMinutes"] = int(tz_offset_minutes)
        response = requests.get(self.rest_url("/api/ranking/clans"), headers=self._auth_headers(), params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()

    def connect(self):
        if not self.auth_token:
            raise RuntimeError("Inicia sesion antes de entrar al modo online")
        if self.sio and not self.sio.connected:
            self.sio.connect(self.server_url, auth={"token": self.auth_token}, transports=["websocket", "polling"])
            self.state.connected = True

    def disconnect(self):
        if self.sio and self.sio.connected:
            self.sio.disconnect()
        self.state.connected = False
        self.state.socket_id = None

    def create_room(self, username="player", platform="pc", fighter_id=None, arena_id="coliseo_de_acero", online_fighter=None):
        if self.sio:
            self.sio.emit(
                "create_room",
                {
                    "username": username,
                    "platform": platform,
                    "arenaId": arena_id,
                    "onlineFighter": online_fighter or {},
                },
            )

    def join_room(self, room_code, username="player", platform="pc", fighter_id=None, arena_id="coliseo_de_acero", online_fighter=None):
        if self.sio:
            self.sio.emit(
                "join_room",
                {
                    "roomCode": room_code,
                    "username": username,
                    "platform": platform,
                    "arenaId": arena_id,
                    "onlineFighter": online_fighter or {},
                },
            )

    def send_input(self, payload):
        if self.sio:
            self.sio.emit("player_input", payload)

    def send_attack(self, attack_type):
        if self.sio:
            self.sio.emit("player_attack", {"attackType": attack_type})

    def send_block(self, active):
        if self.sio:
            self.sio.emit("player_block", {"active": active})

    def send_dodge(self):
        if self.sio:
            self.sio.emit("player_dodge", {})

    def send_hit(self, payload):
        if self.sio:
            self.sio.emit("player_hit", payload)

    def leave_room(self):
        if self.sio:
            self.sio.emit("leave_room", {})
        self.state.room_code = None
