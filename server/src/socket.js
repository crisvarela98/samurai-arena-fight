const fs = require("fs");
const path = require("path");
const { Server } = require("socket.io");
const { createRoom, joinRoom, removePlayerFromRoom, markRoomFinished } = require("./services/room.service");
const { saveMatchResult } = require("./services/match.service");
const { upsertRanking } = require("./services/ranking.service");
const { verifyToken } = require("./middleware/auth.middleware");

const roomState = new Map();
const onlineCatalogPath = path.resolve(__dirname, "../../client/data/online/online_fighters.json");
const defaultOnlinePreset = {
  fighter_name: "Sombra del Cuervo",
  sprite_sheet: "assets/fighters/story/ash_hunter_sheet.png",
  portrait: "assets/fighters/portraits/story/ash_hunter_portrait.png",
};

function loadOnlinePresets() {
  try {
    const raw = fs.readFileSync(onlineCatalogPath, "utf-8");
    const parsed = JSON.parse(raw);
    return parsed.clan_presets || {};
  } catch (_error) {
    return {};
  }
}

const onlineClanPresets = loadOnlinePresets();

function roomSnapshot(roomCode) {
  return roomState.get(roomCode);
}

function clampNumber(value, minimum, maximum, fallback) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? Math.max(minimum, Math.min(maximum, numeric)) : fallback;
}

function onlineClanPreset(clanId) {
  return onlineClanPresets[clanId] || onlineClanPresets.cuervo_negro || defaultOnlinePreset;
}

function sanitizeOnlineFighter(payload = {}, accountUsername = "player") {
  const fighter = payload.onlineFighter || {};
  const clanId = String(fighter.clan_id || fighter.clanId || "cuervo_negro").slice(0, 40);
  const preset = onlineClanPreset(clanId);
  const color = Array.isArray(fighter.color) ? fighter.color.slice(0, 3).map((value) => clampNumber(value, 0, 255, 120)) : [170, 48, 52];
  return {
    username: String(fighter.username || accountUsername).trim().slice(0, 24) || accountUsername,
    fighterName: String(preset.fighter_name || "Guerrero Online").slice(0, 40),
    clanId,
    clanName: String(fighter.clan_name || fighter.clanName || "Clan desconocido").slice(0, 80),
    weaponId: String(fighter.weapon_id || fighter.weaponId || "katana").slice(0, 40),
    weaponName: String(fighter.weapon_name || fighter.weaponName || "Katana").slice(0, 80),
    color,
    maxHealth: clampNumber(fighter.max_health || fighter.maxHealth, 70, 180, 115),
    maxStamina: clampNumber(fighter.max_stamina || fighter.maxStamina, 60, 160, 100),
    speed: clampNumber(fighter.speed, 150, 285, 220),
    attackPower: clampNumber(fighter.attack_power || fighter.attackPower, 8, 32, 18),
    defense: clampNumber(fighter.defense, 1, 18, 8),
    range: clampNumber(fighter.range, 45, 110, 72),
    spriteSheet: String(preset.sprite_sheet || defaultOnlinePreset.sprite_sheet),
    portrait: String(preset.portrait || defaultOnlinePreset.portrait),
    weapon: fighter.weapon || null,
  };
}

function buildPlayer(socket, payload = {}) {
  const profile = sanitizeOnlineFighter(payload, socket.user?.username || "player");
  return {
    socketId: socket.id,
    userId: socket.user?.sub || null,
    username: profile.username,
    fighterName: profile.fighterName,
    platform: payload.platform || "pc",
    fighterId: "online_custom",
    arenaId: payload.arenaId || "coliseo_de_acero",
    clanId: profile.clanId,
    clanName: profile.clanName,
    weaponId: profile.weaponId,
    weaponName: profile.weaponName,
    color: profile.color,
    maxHealth: profile.maxHealth,
    maxStamina: profile.maxStamina,
    speed: profile.speed,
    attackPower: profile.attackPower,
    defense: profile.defense,
    range: profile.range,
    spriteSheet: profile.spriteSheet,
    portrait: profile.portrait,
    weapon: profile.weapon,
    health: profile.maxHealth,
    stamina: profile.maxStamina,
    roundWins: 0,
  };
}

function playersPayload(room) {
  return room.players.map((player) => ({
    socketId: player.socketId,
    username: player.username,
    platform: player.platform,
    fighterId: player.fighterId,
    arenaId: player.arenaId,
    clanId: player.clanId,
    clanName: player.clanName,
    fighterName: player.fighterName,
    weaponId: player.weaponId,
    weaponName: player.weaponName,
    color: player.color,
    maxHealth: player.maxHealth,
    maxStamina: player.maxStamina,
    speed: player.speed,
    attackPower: player.attackPower,
    defense: player.defense,
    range: player.range,
    spriteSheet: player.spriteSheet,
    portrait: player.portrait,
    weapon: player.weapon,
    health: player.health,
    stamina: player.stamina,
    roundWins: player.roundWins || 0,
  }));
}

function findRoomBySocketId(socketId) {
  return [...roomState.values()].find((item) => item.players.some((player) => player.socketId === socketId));
}

function initSocket(server) {
  const io = new Server(server, {
    cors: {
      origin: process.env.CLIENT_URL || "*",
      credentials: true,
    },
  });

  io.use((socket, next) => {
    try {
      socket.user = verifyToken(socket.handshake.auth?.token);
      next();
    } catch (_error) {
      next(new Error("Sesion invalida. Inicia sesion para jugar online."));
    }
  });

  io.on("connection", (socket) => {
    socket.on("create_room", async (payload = {}) => {
      const host = buildPlayer(socket, payload);
      const room = await createRoom({
        username: host.username,
        userId: host.userId,
        clanId: host.clanId,
        weaponId: host.weaponId,
        color: host.color,
      });
      roomState.set(room.roomCode, {
        roomCode: room.roomCode,
        players: [host],
        status: "waiting",
        arenaId: host.arenaId,
        currentRound: 1,
      });
      const snapshot = roomSnapshot(room.roomCode);
      socket.join(room.roomCode);
      socket.emit("room_created", {
        roomCode: room.roomCode,
        status: "waiting",
        arenaId: host.arenaId,
        players: playersPayload(snapshot),
      });
      socket.emit("waiting_for_player", {
        roomCode: room.roomCode,
        arenaId: host.arenaId,
        players: playersPayload(snapshot),
      });
    });

    socket.on("join_room", async (payload = {}) => {
      const roomCode = String(payload.roomCode || "").trim().toUpperCase();
      const snapshot = roomSnapshot(roomCode);
      if (!snapshot) {
        socket.emit("error_message", { message: "Sala no encontrada" });
        return;
      }
      if (snapshot.players.length >= 2) {
        socket.emit("error_message", { message: "La sala ya esta completa" });
        return;
      }
      const guest = buildPlayer(socket, payload);
      await joinRoom({
        roomCode,
        username: guest.username,
        userId: guest.userId,
        clanId: guest.clanId,
        weaponId: guest.weaponId,
        color: guest.color,
      });
      snapshot.players.push(guest);
      snapshot.status = "fighting";
      snapshot.arenaId = snapshot.players[0]?.arenaId || guest.arenaId;
      socket.join(roomCode);
      socket.emit("room_joined", {
        roomCode,
        status: "fighting",
        arenaId: snapshot.arenaId,
        players: playersPayload(snapshot),
      });
      io.to(roomCode).emit("match_started", {
        roomCode,
        arenaId: snapshot.arenaId,
        currentRound: snapshot.currentRound || 1,
        players: playersPayload(snapshot),
      });
    });

    socket.on("player_input", (payload = {}) => {
      const room = findRoomBySocketId(socket.id);
      if (!room) return;
      socket.to(room.roomCode).emit("opponent_input", payload);
    });

    socket.on("player_attack", (payload = {}) => {
      const room = findRoomBySocketId(socket.id);
      if (!room) return;
      socket.to(room.roomCode).emit("opponent_attack", payload);
    });

    socket.on("player_block", (payload = {}) => {
      const room = findRoomBySocketId(socket.id);
      if (!room) return;
      socket.to(room.roomCode).emit("opponent_block", payload);
    });

    socket.on("player_dodge", (payload = {}) => {
      const room = findRoomBySocketId(socket.id);
      if (!room) return;
      socket.to(room.roomCode).emit("opponent_dodge", payload);
    });

    socket.on("player_hit", async (payload = {}) => {
      const room = findRoomBySocketId(socket.id);
      if (!room) return;
      const attacker = room.players.find((player) => player.socketId === socket.id);
      const target = room.players.find((player) => player.socketId !== socket.id);
      if (!target) return;

      const damage = clampNumber(payload.damage, 1, 40, 1);
      target.health = Math.max(0, target.health - damage);
      io.to(room.roomCode).emit("fighter_hit", {
        attackerSocketId: attacker?.socketId || socket.id,
        defenderSocketId: target.socketId,
        attackType: payload.attackType || "attack_light",
        damage,
        knockback: payload.knockback || 0,
        blocked: Boolean(payload.blocked),
        defenderHealth: target.health,
      });
      io.to(room.roomCode).emit("health_update", {
        players: playersPayload(room),
      });
      if (target.health === 0) {
        await finishRound(io, room, attacker, target);
      }
    });

    socket.on("leave_room", async () => {
      await handleLeave(socket, io);
    });

    socket.on("disconnect", async () => {
      await handleLeave(socket, io, true);
    });
  });
}

async function finishMatch(io, room, winner, loser) {
  room.status = "finished";
  await markRoomFinished(room.roomCode);
  await saveMatchResult({
    roomCode: room.roomCode,
    player1: room.players[0]?.username || "player1",
    player2: room.players[1]?.username || "player2",
    player1Clan: room.players[0]?.clanId || "unknown",
    player2Clan: room.players[1]?.clanId || "unknown",
    player1Weapon: room.players[0]?.weaponId || "unknown",
    player2Weapon: room.players[1]?.weaponId || "unknown",
    winner: winner?.username || "winner",
    loser: loser?.username || "loser",
    duration: 0,
  });
  await upsertRanking(winner, loser);
  io.to(room.roomCode).emit("match_finished", {
    roomCode: room.roomCode,
    winnerSocketId: winner?.socketId || null,
    loserSocketId: loser?.socketId || null,
    winner: winner?.username || "winner",
    loser: loser?.username || "loser",
  });
  roomState.delete(room.roomCode);
}

async function finishRound(io, room, winner, loser) {
  if (!winner || !loser) return;
  winner.roundWins = (winner.roundWins || 0) + 1;
  io.to(room.roomCode).emit("round_finished", {
    roomCode: room.roomCode,
    currentRound: room.currentRound || 1,
    winnerSocketId: winner.socketId,
    loserSocketId: loser.socketId,
    players: playersPayload(room),
  });

  if ((winner.roundWins || 0) >= 2) {
    await finishMatch(io, room, winner, loser);
    return;
  }

  room.currentRound = (room.currentRound || 1) + 1;
  room.players.forEach((player) => {
    player.health = player.maxHealth;
    player.stamina = player.maxStamina;
  });

  io.to(room.roomCode).emit("round_started", {
    roomCode: room.roomCode,
    currentRound: room.currentRound,
    players: playersPayload(room),
  });
}

async function handleLeave(socket, io, disconnected = false) {
  const room = findRoomBySocketId(socket.id);
  if (!room) return;
  const leaver = room.players.find((player) => player.socketId === socket.id);
  const rival = room.players.find((player) => player.socketId !== socket.id);
  room.players = room.players.filter((player) => player.socketId !== socket.id);
  await removePlayerFromRoom(room.roomCode, leaver?.username || "player");
  if (rival) {
    io.to(room.roomCode).emit("opponent_left", {
      leaverSocketId: leaver?.socketId || socket.id,
      message: disconnected ? "El rival se desconecto" : "El rival salio",
    });
    await finishMatch(io, room, rival, leaver || { username: "player" });
  } else {
    roomState.delete(room.roomCode);
  }
}

module.exports = { initSocket };
