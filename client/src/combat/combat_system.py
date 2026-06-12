from src.combat.moves import ATTACKS


class CombatSystem:
    def __init__(self, fighter_a, fighter_b, arena, audio=None):
        self.fighter_a = fighter_a
        self.fighter_b = fighter_b
        self.arena = arena
        self.audio = audio
        self.round_finished = False
        self.winner = None

    def update(self, dt):
        self.fighter_a.update(dt, self.arena["floor_y"], (0, 1280))
        self.fighter_b.update(dt, self.arena["floor_y"], (0, 1280))
        self._resolve_overlap()
        self._resolve_hits(self.fighter_a, self.fighter_b)
        self._resolve_hits(self.fighter_b, self.fighter_a)
        if self.fighter_a.state == "defeated" or self.fighter_b.state == "defeated":
            self.round_finished = True
            self.winner = self.fighter_a if self.fighter_b.state == "defeated" else self.fighter_b

    def _resolve_overlap(self):
        if self.fighter_a.rect.colliderect(self.fighter_b.rect):
            overlap = self.fighter_a.rect.centerx - self.fighter_b.rect.centerx
            push = 1 if overlap < 0 else -1
            self.fighter_a.rect.x += push * 2
            self.fighter_b.rect.x -= push * 2

    def _resolve_hits(self, attacker, defender):
        if attacker.state not in ATTACKS:
            return
        info = ATTACKS[attacker.state]
        hit_rect = attacker.hitbox.rect.inflate(info["range"] - attacker.hitbox.width, 8)
        if hit_rect.colliderect(defender.rect):
            dealt = defender.take_damage(info["damage"] + attacker.stats.attack_power // 5, info["knockback"])
            if dealt:
                if self.audio:
                    self.audio.play_hit(attacker.state)
                defender.velocity_x += info["knockback"] * (-1 if attacker.facing == 1 else 1)
                attacker.state = "idle"
