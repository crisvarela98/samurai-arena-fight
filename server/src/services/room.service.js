const Room = require("../models/Room");

function makeRoomCode() {
  return Math.random().toString(36).slice(2, 8).toUpperCase();
}

async function createRoom({ username }) {
  const room = await Room.create({
    roomCode: makeRoomCode(),
    players: [username],
    status: "waiting",
  });
  return room;
}

async function joinRoom({ roomCode, username }) {
  const room = await Room.findOne({ roomCode });
  if (!room) {
    throw new Error("Room not found");
  }
  room.players.push(username);
  room.status = "fighting";
  await room.save();
  return room;
}

async function removePlayerFromRoom(roomCode, username) {
  const room = await Room.findOne({ roomCode });
  if (!room) return null;
  room.players = room.players.filter((player) => player !== username);
  if (room.players.length === 0) {
    room.status = "finished";
  }
  await room.save();
  return room;
}

async function markRoomFinished(roomCode) {
  const room = await Room.findOne({ roomCode });
  if (!room) return null;
  room.status = "finished";
  await room.save();
  return room;
}

module.exports = { createRoom, joinRoom, removePlayerFromRoom, markRoomFinished };
