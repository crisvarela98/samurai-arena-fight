const { Server } = require("socket.io");
const { createRoom, joinRoom, removePlayerFromRoom, markRoomFinished } = require("./services/room.service");
const { saveMatchResult } = require("./services/match.service");
const { upsertRanking } = require("./services/ranking.service");

const roomState = new Map();

function roomSnapshot(roomCode) {
  return roomState.get(roomCode);
}

function buildPlayer(socket, payload = {}) {
  return {
    socketId: socket.id,
    username: payload.username || "player",
    platform: payload.platform || "pc",
    fighterId: payload.fighterId || "kenji",
    arenaId: payload.arenaId || "coliseo_de_acero",
    health: 100,
    stamina: 100,
  };
}

function playersPayload(room) {
  return room.players.map((player) => ({
    socketId: player.socketId,
    username: player.username,
    platform: player.platform,
    fighterId: player.fighterId,
    arenaId: player.arenaId,
    health: player.health,
    stamina: player.stamina,
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

  io.on("connection", (socket) => {
    socket.on("create_room", async (payload = {}) => {
      const room = await createRoom({ username: payload.username || "player", socketId: socket.id });
      const host = buildPlayer(socket, payload);
      roomState.set(room.roomCode, {
        roomCode: room.roomCode,
        players: [host],
        status: "waiting",
        arenaId: host.arenaId,
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
      await joinRoom({ roomCode, username: payload.username || "player", socketId: socket.id });
      const guest = buildPlayer(socket, payload);
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

      target.health = Math.max(0, payload.health ?? target.health - (payload.damage || 0));
      io.to(room.roomCode).emit("fighter_hit", {
        attackerSocketId: attacker?.socketId || socket.id,
        defenderSocketId: target.socketId,
        attackType: payload.attackType || "attack_light",
        damage: payload.damage || 0,
        knockback: payload.knockback || 0,
        blocked: Boolean(payload.blocked),
        defenderHealth: target.health,
      });
      io.to(room.roomCode).emit("health_update", {
        players: playersPayload(room),
      });
      if (target.health === 0) {
        await finishMatch(io, room, attacker, target);
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
    winner: winner?.username || "winner",
    loser: loser?.username || "loser",
    duration: 0,
  });
  await upsertRanking(winner?.username || "winner", loser?.username || "loser");
  io.to(room.roomCode).emit("match_finished", {
    roomCode: room.roomCode,
    winnerSocketId: winner?.socketId || null,
    loserSocketId: loser?.socketId || null,
    winner: winner?.username || "winner",
    loser: loser?.username || "loser",
  });
  roomState.delete(room.roomCode);
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
