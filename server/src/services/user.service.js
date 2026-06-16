const mongoose = require("mongoose");
const User = require("../models/User");

const memoryUsers = new Map();
const HONOR_PER_LEVEL = 250;

function databaseReady() {
  return mongoose.connection.readyState === 1;
}

function normalizeStoryProgress(storyProgress = {}) {
  const progress = storyProgress || {};
  return {
    first_time_completed: Boolean(progress.first_time_completed),
    story_act: Math.max(1, Number(progress.story_act || 1)),
    story_mission: Math.max(0, Number(progress.story_mission || 0)),
    unlocked_modes: Array.isArray(progress.unlocked_modes) ? progress.unlocked_modes : [],
  };
}

function computeHonorPoints(source = {}) {
  return Math.max(
    0,
    Math.floor(
      Math.max(
        Number(source.honorPoints ?? 0),
        Number(source.rankingPoints ?? 0),
      ),
    ),
  );
}

function publicUser(user) {
  if (!user) return null;
  const source = user.toObject ? user.toObject() : user;
  const normalizedStoryProgress = normalizeStoryProgress(source.storyProgress);
  const honorPoints = computeHonorPoints(source);
  return {
    id: String(source._id || source.id),
    username: source.username,
    email: source.email,
    honorPoints,
    wins: source.wins || 0,
    losses: source.losses || 0,
    rankingPoints: source.rankingPoints || 0,
    level: Math.max(1, Math.floor(honorPoints / HONOR_PER_LEVEL) + 1),
    selectedClan: source.selectedClan || "cuervo_negro",
    selectedWeapon: source.selectedWeapon || "katana",
    selectedColor: source.selectedColor || [170, 48, 52],
    storyProgress: normalizedStoryProgress,
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
  const user = {
    id,
    _id: id,
    ...payload,
    honorPoints: 0,
    wins: 0,
    losses: 0,
    rankingPoints: 0,
    storyProgress: normalizeStoryProgress(payload.storyProgress),
  };
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

module.exports = {
  databaseReady,
  publicUser,
  findUserByIdentity,
  findUserById,
  createUser,
  updateUser,
  normalizeStoryProgress,
  computeHonorPoints,
};
