from dataclasses import dataclass


@dataclass
class Weapon:
    id: str
    name: str
    damage_light: int
    damage_heavy: int
    stamina_cost: int
    range: int
    cooldown: float
