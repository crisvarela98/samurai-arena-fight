const KEY_PREFIX = "samurai-arena-fight-web";

const DEFAULT_PROGRESS = {
  first_time_completed: false,
  story_act: 1,
  story_mission: 0,
  unlocked_modes: ["Historia", "Juego rapido"],
  selected_story_character: "kenji",
};

const DEFAULT_SETTINGS = {
  apiBaseUrl: "",
  socketUrl: "",
  musicMuted: false,
  fxMuted: false,
  fullscreen: false,
  playerName: "player",
};

const DEFAULT_AUTH = {
  token: "",
  user: null,
};

const DEFAULT_ONLINE_PROFILE = {
  username: "guerrero",
  clan_id: "cuervo_negro",
  weapon_id: "katana",
  color: [170, 48, 52],
};

function load(key, fallback) {
  try {
    const raw = localStorage.getItem(`${KEY_PREFIX}:${key}`);
    if (!raw) return structuredClone(fallback);
    return { ...structuredClone(fallback), ...JSON.parse(raw) };
  } catch (_error) {
    return structuredClone(fallback);
  }
}

function save(key, value) {
  localStorage.setItem(`${KEY_PREFIX}:${key}`, JSON.stringify(value));
}

export function loadProgress() {
  return load("progress", DEFAULT_PROGRESS);
}

export function saveProgress(progress) {
  save("progress", progress);
}

export function loadSettings() {
  return load("settings", DEFAULT_SETTINGS);
}

export function saveSettings(settings) {
  save("settings", settings);
}

export function loadAuth() {
  return load("auth", DEFAULT_AUTH);
}

export function saveAuth(auth) {
  save("auth", auth);
}

export function clearAuth() {
  save("auth", DEFAULT_AUTH);
}

export function loadOnlineProfile() {
  return load("online-profile", DEFAULT_ONLINE_PROFILE);
}

export function saveOnlineProfile(profile) {
  save("online-profile", profile);
}

export function buildCompletedMissionProgress(missionNumber) {
  const unlocked = new Set(["Historia", "Juego rapido"]);
  if (missionNumber >= 1) unlocked.add("Online");
  return {
    first_time_completed: missionNumber >= 1,
    story_act: 1,
    story_mission: missionNumber,
    unlocked_modes: [...unlocked],
  };
}
