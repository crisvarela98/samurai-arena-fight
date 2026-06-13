const mongoose = require("mongoose");
const User = require("../models/User");

const memoryUsers = new Map();

function databaseReady() {
  return mongoose.connection.readyState === 1;
}

function publicUser(user) {
  if (!user) return null;
  const source = user.toObject ? user.toObject() : user;
  return {
    id: String(source._id || source.id),
    username: source.username,
    email: source.email,
    coins: source.coins || 0,
    wins: source.wins || 0,
    losses: source.losses || 0,
    rankingPoints: source.rankingPoints || 0,
    selectedClan: source.selectedClan || "cuervo_negro",
    selectedWeapon: source.selectedWeapon || "katana",
    selectedColor: source.selectedColor || [170, 48, 52],
    storyProgress: source.storyProgress || {},
    unlockedClans: source.unlockedClans || ["cuervo_negro"],
    unlockedWeapons: source.unlockedWeapons || ["katana"],
  };
}

async function findUserByIdentity(identity) {
  const normalized = String(identity || "").trim().toLowerCase();
  if (databaseReady()) {
    return User.findOne({ $or: [{ email: normalized }, { username: normalized }] });
  }
  return [...memoryUsers.values()].find(
    (user) => user.email === normalized || user.username.toLowerCase() === normalized
  ) || null;
}

async function findUserById(id) {
  if (databaseReady()) return User.findById(id);
  return memoryUsers.get(String(id)) || null;
}

async function createUser(payload) {
  if (databaseReady()) return User.create(payload);
  const id = new mongoose.Types.ObjectId().toString();
  const user = { id, _id: id, ...payload, coins: 0, wins: 0, losses: 0, rankingPoints: 0 };
  memoryUsers.set(id, user);
  return user;
}

async function updateUser(id, changes) {
  if (databaseReady()) return User.findByIdAndUpdate(id, changes, { new: true });
  const user = memoryUsers.get(String(id));
  if (!user) return null;
  Object.assign(user, changes);
  return user;
}

module.exports = { databaseReady, publicUser, findUserByIdentity, findUserById, createUser, updateUser };
