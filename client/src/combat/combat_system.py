from src.combat.moves import ATTACKS


def update_fighter_facing(fighter_a, fighter_b):
    if fighter_a.rect.centerx == fighter_b.rect.centerx:
        return
    fighter_a_faces = 1 if fighter_a.rect.centerx < fighter_b.rect.centerx else -1
    fighter_b_faces = -fighter_a_faces
    if fighter_a.state not in ATTACKS and fighter_a.state not in {"dodge", "defeated"}:
        fighter_a.facing = fighter_a_faces
    if fighter_b.state not in ATTACKS and fighter_b.state not in {"dodge", "defeated"}:
        fighter_b.facing = fighter_b_faces


def resolve_fighter_collision(fighter_a, fighter_b, bounds=(0, 1280)):
    body_a = fighter_a.body_collision_rect
    body_b = fighter_b.body_collision_rect
    if not body_a.colliderect(body_b):
        update_fighter_facing(fighter_a, fighter_b)
        return

    if fighter_a.rect.bottom < fighter_b.rect.top + 44 or fighter_b.rect.bottom < fighter_a.rect.top + 44:
        update_fighter_facing(fighter_a, fighter_b)
        return

    if body_a.centerx <= body_b.centerx:
        penetration = body_a.right - body_b.left
        direction = -1
    else:
        penetration = body_b.right - body_a.left
        direction = 1
    if penetration <= 0:
        update_fighter_facing(fighter_a, fighter_b)
        return

    move_a = (penetration + 1) // 2
    move_b = penetration - move_a
    fighter_a.rect.x += direction * move_a
    fighter_b.rect.x -= direction * move_b

    fighter_a.rect.left = max(bounds[0], fighter_a.rect.left)
    fighter_a.rect.right = min(bounds[1], fighter_a.rect.right)
    fighter_b.rect.left = max(bounds[0], fighter_b.rect.left)
    fighter_b.rect.right = min(bounds[1], fighter_b.rect.right)

    body_a = fighter_a.body_collision_rect
    body_b = fighter_b.body_collision_rect
    if body_a.colliderect(body_b):
        if body_a.centerx <= body_b.centerx:
            remaining = body_a.right - body_b.left
            if fighter_a.rect.left <= bounds[0]:
                fighter_b.rect.x += remaining
            else:
                fighter_a.rect.x -= remaining
        else:
            remaining = body_b.right - body_a.left
            if fighter_a.rect.right >= bounds[1]:
                fighter_b.rect.x -= remaining
            else:
                fighter_a.rect.x += remaining
        fighter_a.rect.left = max(bounds[0], fighter_a.rect.left)
        fighter_a.rect.right = min(bounds[1], fighter_a.rect.right)
        fighter_b.rect.left = max(bounds[0], fighter_b.rect.left)
        fighter_b.rect.right = min(bounds[1], fighter_b.rect.right)

    if direction < 0:
        if fighter_a.velocity_x > 0:
            fighter_a.velocity_x = 0
        if fighter_b.velocity_x < 0:
            fighter_b.velocity_x = 0
    else:
        if fighter_a.velocity_x < 0:
            fighter_a.velocity_x = 0
        if fighter_b.velocity_x > 0:
            fighter_b.velocity_x = 0

    fighter_a.sync_position_from_rect()
    fighter_b.sync_position_from_rect()
    update_fighter_facing(fighter_a, fighter_b)


class CombatSystem:
    def __init__(self, fighter_a, fighter_b, arena, audio=None):
        self.fighter_a = fighter_a
        self.fighter_b = fighter_b
        self.arena = arena
        self.audio = audio
        self.round_finished = False
        self.winner = None
        self.hitstop_timer = 0.0

    def update(self, dt):
        if self.hitstop_timer > 0:
            self.hitstop_timer = max(0.0, self.hitstop_timer - dt)
            return
        self.fighter_a.update(dt, self.arena["floor_y"], (0, 1280))
        self.fighter_b.update(dt, self.arena["floor_y"], (0, 1280))
        resolve_fighter_collision(self.fighter_a, self.fighter_b)
        self._resolve_hits(self.fighter_a, self.fighter_b)
        self._resolve_hits(self.fighter_b, self.fighter_a)
        if self.fighter_a.state == "defeated" or self.fighter_b.state == "defeated":
            self.round_finished = True
            self.winner = self.fighter_a if self.fighter_b.state == "defeated" else self.fighter_b

    def _resolve_hits(self, attacker, defender):
        if not attacker.can_connect_attack():
            return
        info = ATTACKS[attacker.state]
        hit_rect = attacker.attack_hitbox_rect()
        if hit_rect.colliderect(defender.hurtbox_rect):
            damage = max(1, info["damage"] + attacker.stats.attack_power // 5 - defender.stats.defense // 4)
            dealt = defender.take_damage(damage, info["knockback"] * attacker.facing)
            attacker.mark_attack_connected()
            if dealt:
                if self.audio:
                    self.audio.play_hit(attacker.state)
                self.hitstop_timer = max(self.hitstop_timer, info["hitstop"])
