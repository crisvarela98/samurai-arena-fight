import json
from pathlib import Path


def load_online_catalog(client_dir):
    data_dir = Path(client_dir) / "data" / "online"
    clans = json.loads((data_dir / "clans.json").read_text(encoding="utf-8"))
    weapons = json.loads((data_dir / "online_weapons.json").read_text(encoding="utf-8"))
    fighters = json.loads((data_dir / "online_fighters.json").read_text(encoding="utf-8"))
    return clans, weapons, fighters


def get_online_clan_preset(client_dir, clan_id):
    _, _, fighters = load_online_catalog(client_dir)
    presets = fighters.get("clan_presets", {})
    return presets.get(clan_id) or presets.get("cuervo_negro") or {}


def build_online_fighter(client_dir, username, clan_id, weapon_id, color):
    clans, weapons, fighters = load_online_catalog(client_dir)
    clan = next(item for item in clans if item["id"] == clan_id)
    weapon = next(item for item in weapons if item["id"] == weapon_id)
    stats = dict(fighters["base"])
    preset = get_online_clan_preset(client_dir, clan_id)
    for key, value in clan.get("bonuses", {}).items():
        stats[key] = stats.get(key, 0) + value
    for key, value in weapon.get("bonuses", {}).items():
        stats[key] = stats.get(key, 0) + value
    stats["range"] = weapon["range"]
    return {
        "username": username.strip() or "guerrero",
        "clan_id": clan_id,
        "clan_name": clan["name"],
        "weapon_id": weapon_id,
        "weapon_name": weapon["name"],
        "color": list(color),
        "max_health": max(70, int(stats["max_health"])),
        "max_stamina": max(60, int(stats["max_stamina"])),
        "speed": max(150, int(stats["speed"])),
        "attack_power": max(8, int(stats["attack_power"])),
        "defense": max(1, int(stats["defense"])),
        "range": int(stats["range"]),
        "fighter_name": preset.get("fighter_name", clan["name"]),
        "sprite_sheet": preset.get("sprite_sheet", ""),
        "portrait": preset.get("portrait", ""),
        "frame_count": int(preset.get("frame_count", 7) or 7),
        "weapon": {key: weapon[key] for key in ("id", "name", "damage_light", "damage_heavy", "stamina_cost", "range", "cooldown")},
    }
