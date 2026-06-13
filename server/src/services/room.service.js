const Room = require("../models/Room");
const { databaseReady } = require("./user.service");

const memoryRooms = new Map();

function makeRoomCode() {
  return Math.random().toString(36).slice(2, 8).toUpperCase();
}

async function createRoom({ username, userId = null, clanId, weaponId, color }) {
  const room = {
    roomCode: makeRoomCode(),
    players: [{ userId, username, clanId, weaponId, color }],
    status: "waiting",
  };
  if (databaseReady()) return Room.create(room);
  memoryRooms.set(room.roomCode, room);
  return room;
}

async function joinRoom({ roomCode, username, userId = null, clanId, weaponId, color }) {
  const room = databaseReady() ? await Room.findOne({ roomCode }) : memoryRooms.get(roomCode);
  if (!room) {
    throw new Error("Room not found");
  }
  room.players.push({ userId, username, clanId, weaponId, color });
  room.status = "fighting";
  if (room.save) await room.save();
  return room;
}

async function removePlayerFromRoom(roomCode, username) {
  const room = databaseReady() ? await Room.findOne({ roomCode }) : memoryRooms.get(roomCode);
  if (!room) return null;
  room.players = room.players.filter((player) => player.username !== username);
  if (room.players.length === 0) {
    room.status = "finished";
  }
  if (room.save) await room.save();
  return room;
}

async function markRoomFinished(roomCode) {
  const room = databaseReady() ? await Room.findOne({ roomCode }) : memoryRooms.get(roomCode);
  if (!room) return null;
  room.status = "finished";
  if (room.save) await room.save();
  return room;
}

async function listRooms() {
  if (databaseReady()) return Room.find().sort({ createdAt: -1 }).limit(20).lean();
  return [...memoryRooms.values()];
}

module.exports = { createRoom, joinRoom, removePlayerFromRoom, markRoomFinished, listRooms };
