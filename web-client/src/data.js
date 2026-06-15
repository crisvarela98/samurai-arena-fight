function assetUrl(relativePath) {
  if (!relativePath) return "";
  return `/game/${String(relativePath).replace(/^\/+/, "")}`;
}

async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`No se pudo cargar ${path}`);
  }
  return response.json();
}

function buildClans(onlineConfig) {
  return Object.entries(onlineConfig.clan_presets || {}).map(([id, value]) => ({
    id,
    name: value.fighter_name,
    portrait: assetUrl(value.portrait),
    portraitUrl: assetUrl(value.portrait),
    color: value.default_color || [170, 48, 52],
    sprite_sheet: assetUrl(value.sprite_sheet),
    spriteUrl: assetUrl(value.sprite_sheet),
  }));
}

export async function loadGameData() {
  const [
    fighters,
    arenas,
    missions,
    enemies,
    cutscenes,
    storyFighter,
    onlineFighters,
    onlineWeapons,
  ] = await Promise.all([
    loadJson("/game/data/fighters.json"),
    loadJson("/game/data/arenas.json"),
    loadJson("/game/data/story/missions.json"),
    loadJson("/game/data/story/enemies.json"),
    loadJson("/game/data/story/cutscenes.json"),
    loadJson("/game/data/story/story_fighter.json"),
    loadJson("/game/data/online/online_fighters.json"),
    loadJson("/game/data/online/online_weapons.json"),
  ]);

  const mappedFighters = fighters.map((fighter) => ({
    ...fighter,
    portraitUrl: assetUrl(fighter.portrait),
    spriteUrl: assetUrl(fighter.sprite_sheet),
  }));
  const mappedEnemies = enemies.map((enemy) => ({
    ...enemy,
    portraitUrl: assetUrl(enemy.portrait),
    spriteUrl: assetUrl(enemy.sprite_sheet),
  }));
  const missionsById = Object.fromEntries(missions.map((item) => [item.id, item]));
  const enemiesById = Object.fromEntries(mappedEnemies.map((item) => [item.id, item]));
  const arenasById = Object.fromEntries(arenas.map((item) => [item.id, item]));
  const fightersById = Object.fromEntries(mappedFighters.map((item) => [item.id, item]));
  const cutscenesById = Object.fromEntries(cutscenes.map((item) => [item.id, item]));
  const weaponsById = Object.fromEntries(onlineWeapons.map((item) => [item.id, item]));

  return {
    fighters: mappedFighters,
    arenas: arenas.map((arena) => ({
      ...arena,
      backgroundUrl: assetUrl(arena.background),
      floorUrl: assetUrl(arena.floor),
    })),
    missions,
    enemies: mappedEnemies,
    cutscenes,
    storyFighter: {
      ...storyFighter,
      portraitUrl: assetUrl(storyFighter.portrait),
      spriteUrl: assetUrl(storyFighter.sprite_sheet),
    },
    onlineFighters,
    onlineWeapons,
    clans: buildClans(onlineFighters),
    missionsById,
    enemiesById,
    arenasById,
    fightersById,
    cutscenesById,
    weaponsById,
    assetUrl,
  };
}
