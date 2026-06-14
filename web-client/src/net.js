import { io } from "socket.io-client";

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export class ApiClient {
  constructor(getConfig, getToken) {
    this.getConfig = getConfig;
    this.getToken = getToken;
  }

  async request(path, options = {}) {
    const { apiBaseUrl } = this.getConfig();
    const response = await fetch(`${apiBaseUrl}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(this.getToken()),
        ...(options.headers || {}),
      },
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.message || "Error de red");
    }
    return payload;
  }

  login(identity, password) {
    return this.request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ identity, password }),
    });
  }

  register(username, email, password) {
    return this.request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    });
  }

  me() {
    return this.request("/api/auth/me");
  }

  rooms() {
    return this.request("/api/rooms");
  }

  ranking() {
    return this.request("/api/ranking");
  }

  updateProgress(storyProgress, profile) {
    return this.request("/api/users/me/progress", {
      method: "PUT",
      body: JSON.stringify({
        storyProgress,
        selectedClan: profile?.clan_id || "cuervo_negro",
        selectedWeapon: profile?.weapon_id || "katana",
        selectedColor: profile?.color || [170, 48, 52],
      }),
    });
  }
}

export class RealtimeClient {
  constructor(getConfig, getToken) {
    this.getConfig = getConfig;
    this.getToken = getToken;
    this.socket = null;
    this.handlers = new Map();
    this.state = {
      socketId: null,
      roomCode: null,
      connected: false,
    };
  }

  on(event, callback) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event).add(callback);
    return () => this.handlers.get(event)?.delete(callback);
  }

  emitLocal(event, payload) {
    this.handlers.get(event)?.forEach((callback) => callback(payload));
  }

  connect() {
    if (this.socket?.connected) return this.socket;
    const token = this.getToken();
    if (!token) throw new Error("Necesitás iniciar sesión para jugar online.");
    const { socketUrl } = this.getConfig();
    this.socket = io(socketUrl, {
      transports: ["websocket", "polling"],
      auth: { token },
    });
    this.socket.on("connect", () => {
      this.state.connected = true;
      this.state.socketId = this.socket.id;
      this.emitLocal("connect", { socketId: this.socket.id });
    });
    this.socket.on("disconnect", () => {
      this.state.connected = false;
      this.emitLocal("disconnect", {});
    });
    [
      "room_created",
      "waiting_for_player",
      "room_joined",
      "match_started",
      "error_message",
      "opponent_input",
      "opponent_attack",
      "opponent_block",
      "opponent_dodge",
      "fighter_hit",
      "health_update",
      "round_finished",
      "round_started",
      "match_finished",
      "opponent_left",
    ].forEach((event) => {
      this.socket.on(event, (payload) => this.emitLocal(event, payload));
    });
    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.state.connected = false;
    this.state.roomCode = null;
  }

  createRoom(payload) {
    this.connect();
    this.socket.emit("create_room", payload);
  }

  joinRoom(payload) {
    this.connect();
    this.socket.emit("join_room", payload);
  }

  leaveRoom() {
    this.socket?.emit("leave_room");
  }

  sendInput(payload) {
    this.socket?.emit("player_input", payload);
  }

  sendAttack(payload) {
    this.socket?.emit("player_attack", payload);
  }

  sendBlock(payload) {
    this.socket?.emit("player_block", payload);
  }

  sendDodge(payload) {
    this.socket?.emit("player_dodge", payload);
  }

  sendHit(payload) {
    this.socket?.emit("player_hit", payload);
  }
}
