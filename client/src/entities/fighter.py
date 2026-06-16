from dataclasses import dataclass

import pygame

from src.combat.moves import ATTACKS

ATTACK_STATES = frozenset(ATTACKS)


@dataclass
class FighterStats:
    id: str
    name: str
    max_health: int
    max_stamina: int
    speed: int
    attack_power: int
    defense: int
    weapon_id: str
    sprite_sheet: str = ""
    portrait: str = ""
    frame_count: int = 7


class Fighter:
    HEALTH_REGEN_RATE = 0.01
    STAMINA_REGEN_RATE = 0.08
    GRAVITY = 1850
    JUMP_SPEED = 690
    MAX_FALL_SPEED = 980

    def __init__(self, stats, weapon, x, y, color, asset_loader=None):
        self.stats = stats
        self.weapon = weapon
        self.rect = pygame.Rect(x, y, 72, 132)
        self.position_x = float(x)
        self.position_y = float(y)
        self.color = color
        self.facing = 1
        self.velocity_x = 0
        self.velocity_y = 0
        self.on_ground = True
        self.health = stats.max_health
        self.stamina = stats.max_stamina
        self.state = "idle"
        self.attack_timer = 0.0
        self.attack_duration = 0.0
        self.attack_hit_confirmed = False
        self.cooldown_timer = 0.0
        self.blocking = False
        self.crouching = False
        self.invincible_timer = 0.0
        self.hurt_timer = 0.0
        self.dodge_timer = 0.0
        self.landing_timer = 0.0
        self.flash_timer = 0.0
        self.combo_damage = 0
        self.sprite_frames = []
        self.flipped_frames = []
        self.outline_frames = []
        self.flipped_outline_frames = []
        self.animation_frames = {}
        self.flipped_animation_frames = {}
        self.animation_outlines = {}
        self.flipped_animation_outlines = {}
        self.animation_time = 0.0
        self.animation_state = self.state
        self.portrait_image = None
        if asset_loader and stats.sprite_sheet:
            self.sprite_frames = asset_loader.load_sprite_strip(
                stats.sprite_sheet,
                max(1, int(stats.frame_count or 7)),
                scale_height=180,
                chroma_key=(0, 255, 0),
                chroma_tolerance=110,
            )
            self.flipped_frames = [pygame.transform.flip(frame, True, False) for frame in self.sprite_frames]
            self.outline_frames = [self._build_outline(frame) for frame in self.sprite_frames]
            self.flipped_outline_frames = [pygame.transform.flip(frame, True, False) for frame in self.outline_frames]
            self._build_animation_bank()
        if asset_loader and stats.portrait:
            self.portrait_image = asset_loader.load_image(
                stats.portrait,
                trim_alpha=True,
            )

    def reset_for_round(self, x, floor_y, facing):
        self.rect.x = x
        self.rect.bottom = floor_y
        self._sync_position_from_rect()
        self.facing = facing
        self.velocity_x = 0
        self.velocity_y = 0
        self.on_ground = True
        self.health = self.stats.max_health
        self.stamina = self.stats.max_stamina
        self.state = "idle"
        self.attack_timer = 0.0
        self.attack_duration = 0.0
        self.attack_hit_confirmed = False
        self.cooldown_timer = 0.0
        self.blocking = False
        self.crouching = False
        self.invincible_timer = 0.0
        self.hurt_timer = 0.0
        self.dodge_timer = 0.0
        self.landing_timer = 0.0
        self.flash_timer = 0.0
        self.animation_time = 0.0
        self.animation_state = self.state
        self.combo_damage = 0

    def move(self, direction, dt):
        if self.state in ATTACK_STATES or self.state in {"hurt", "dodge", "landing", "defeated"} or self.crouching:
            return
        target_speed = direction * self.stats.speed
        if not self.on_ground:
            target_speed *= 0.72
            self.velocity_x = self._approach(self.velocity_x, target_speed, 980 * dt)
            return
        acceleration = 2200 if direction else 3000
        self.velocity_x = self._approach(self.velocity_x, target_speed, acceleration * dt)
        if direction:
            self._set_state("walk")
        elif not self.blocking:
            self._set_state("idle")

    def jump(self):
        if self.on_ground and self.state not in ATTACK_STATES and self.state not in {"dodge", "hurt", "landing", "defeated"}:
            self.crouching = False
            self.velocity_y = -self.JUMP_SPEED
            self.on_ground = False
            self._set_state("jump")
            return True
        return False

    def crouch(self, active):
        if self.state in ATTACKS and ATTACKS[self.state].get("keep_crouch"):
            self.crouching = True
            return
        self.crouching = active and self.on_ground and self.state not in ATTACK_STATES and self.state not in {"hurt", "dodge", "landing", "defeated"}
        if self.crouching:
            self.velocity_x = 0
            self._set_state("crouch")
        elif self.state == "crouch":
            self._set_state("idle")

    def start_attack(self, attack_name):
        info = ATTACKS.get(attack_name)
        if not info:
            return False
        if info.get("requires_ground", True) and not self.on_ground:
            return False
        if info.get("requires_air") and self.on_ground:
            return False
        if info.get("requires_crouch") and not self.crouching:
            return False
        stamina_cost = info["stamina"]
        if self.cooldown_timer > 0 or self.stamina < stamina_cost or self.state in {"hurt", "dodge", "landing", "defeated"}:
            return False
        duration = info["startup"] + info["active"] + info["recovery"]
        self.crouching = bool(info.get("keep_crouch"))
        self.blocking = False
        self._set_state(attack_name)
        self.attack_timer = duration
        self.attack_duration = duration
        self.attack_hit_confirmed = False
        self.cooldown_timer = max(self.weapon.cooldown, duration)
        self.stamina = max(0, self.stamina - stamina_cost)
        self.velocity_x = info["lunge"] * self.facing
        vertical_cap = info.get("vertical_speed_cap")
        if vertical_cap is not None and self.velocity_y > vertical_cap:
            self.velocity_y = vertical_cap
        return True

    def block(self, active):
        if active:
            self.crouching = False
        self.blocking = active and self.on_ground and self.state not in ATTACK_STATES and self.state not in {"hurt", "dodge", "landing", "defeated"}
        if self.blocking:
            self.velocity_x = self._approach(self.velocity_x, 0, 2800 / 60)
            self._set_state("block")
        elif self.state == "block":
            self._set_state("idle")

    def dodge(self):
        if self.stamina < 18 or not self.on_ground or self.state in ATTACK_STATES or self.state in {"hurt", "dodge", "landing", "defeated"}:
            return False
        self.crouching = False
        self._set_state("dodge")
        self.dodge_timer = 0.32
        self.invincible_timer = 0.24
        self.stamina -= 18
        self.velocity_x = 330 * self.facing
        return True

    def take_damage(self, amount, signed_knockback):
        if self.invincible_timer > 0 or self.state == "defeated":
            return 0
        if self.blocking:
            amount = max(1, int(amount * 0.35))
            signed_knockback = int(signed_knockback * 0.45)
        self.crouching = False
        self.blocking = False
        self.attack_timer = 0.0
        self.attack_duration = 0.0
        self.attack_hit_confirmed = False
        self.health = max(0, self.health - amount)
        self.flash_timer = 0.12
        if self.health <= 0:
            self._set_state("defeated")
            self.hurt_timer = 0.0
        else:
            self._set_state("hurt")
            self.hurt_timer = 0.18 + min(0.12, amount * 0.004)
        self.velocity_x = signed_knockback
        if abs(signed_knockback) >= 250 and self.on_ground:
            self.velocity_y = -78
        return amount

    def apply_network_hit(self, damage, knockback):
        if self.state == "defeated":
            return
        self.crouching = False
        self.blocking = False
        self.attack_timer = 0.0
        self.attack_duration = 0.0
        self.attack_hit_confirmed = False
        self.health = max(0, self.health - damage)
        if self.health <= 0:
            self._set_state("defeated")
            self.hurt_timer = 0.0
        else:
            self._set_state("hurt")
            self.hurt_timer = 0.22
        self.flash_timer = 0.12
        self.velocity_x = knockback

    @property
    def hurtbox_rect(self):
        height = 78 if self.crouching else 112
        width = 56
        return pygame.Rect(self.rect.centerx - width // 2, self.rect.bottom - height, width, height)

    @property
    def body_collision_rect(self):
        height = 74 if self.crouching else 106
        width = 54
        return pygame.Rect(self.rect.centerx - width // 2, self.rect.bottom - height, width, height)

    def attack_hitbox_rect(self):
        info = ATTACKS.get(self.state)
        if not info:
            return pygame.Rect(0, 0, 0, 0)
        if self.facing > 0:
            x = self.rect.centerx + 8
        else:
            x = self.rect.centerx - info["range"] - 8
        return pygame.Rect(x, self.rect.y + info["offset_y"], info["range"], info["height"])

    def attack_phase(self):
        info = ATTACKS.get(self.state)
        if not info or self.attack_duration <= 0:
            return None
        elapsed = self.attack_duration - self.attack_timer
        if elapsed < info["startup"]:
            return "startup"
        if elapsed < info["startup"] + info["active"]:
            return "active"
        return "recovery"

    def can_connect_attack(self):
        return self.attack_phase() == "active" and not self.attack_hit_confirmed

    def mark_attack_connected(self):
        self.attack_hit_confirmed = True

    def sync_position_from_rect(self):
        self._sync_position_from_rect()

    def advance_animation(self, dt):
        if self.animation_state != self.state:
            self.animation_state = self.state
            self.animation_time = 0.0
        else:
            self.animation_time += dt

    def update(self, dt, floor_y, bounds):
        self.advance_animation(dt)
        if self.health > 0:
            self.health = min(self.stats.max_health, self.health + self.stats.max_health * self.HEALTH_REGEN_RATE * dt)
            self.stamina = min(self.stats.max_stamina, self.stamina + self.stats.max_stamina * self.STAMINA_REGEN_RATE * dt)
        if self.cooldown_timer > 0:
            self.cooldown_timer = max(0, self.cooldown_timer - dt)
        if self.invincible_timer > 0:
            self.invincible_timer = max(0, self.invincible_timer - dt)
        if self.flash_timer > 0:
            self.flash_timer = max(0, self.flash_timer - dt)
        if self.hurt_timer > 0:
            self.hurt_timer = max(0, self.hurt_timer - dt)
            if self.hurt_timer == 0 and self.health > 0:
                self._set_state("idle")
        if self.dodge_timer > 0:
            self.dodge_timer = max(0, self.dodge_timer - dt)
            if self.dodge_timer == 0 and self.health > 0:
                self._set_state("idle")
        if self.landing_timer > 0:
            self.landing_timer = max(0, self.landing_timer - dt)
            if self.landing_timer == 0 and self.health > 0:
                self._set_state("idle")
        if self.attack_timer > 0:
            self.attack_timer = max(0, self.attack_timer - dt)
            if self.attack_timer == 0 and self.health > 0:
                self.attack_duration = 0.0
                self.attack_hit_confirmed = False
                self._set_state("idle")

        was_on_ground = self.on_ground
        fall_speed = self.velocity_y
        self.velocity_y = min(self.MAX_FALL_SPEED, self.velocity_y + self.GRAVITY * dt)
        self.position_x += self.velocity_x * dt
        self.position_y += self.velocity_y * dt
        self.rect.x = round(self.position_x)
        self.rect.y = round(self.position_y)

        drag = 0.86 if self.state == "dodge" else 0.91 if self.state in ATTACKS else 0.97 if not self.on_ground else 0.90
        self.velocity_x *= drag
        if abs(self.velocity_x) < 2:
            self.velocity_x = 0

        if self.rect.bottom >= floor_y:
            self.rect.bottom = floor_y
            self.position_y = float(self.rect.y)
            self.velocity_y = 0
            self.on_ground = True
        else:
            self.on_ground = False

        if self.on_ground and not was_on_ground and fall_speed > 220 and self.health > 0:
            self._set_state("landing")
            self.landing_timer = 0.10
        elif not self.on_ground and self.state not in ATTACK_STATES and self.state not in {"hurt", "dodge", "defeated"}:
            self._set_state("jump")
            self.crouching = False
        elif self.on_ground and self.state == "jump":
            self._set_state("crouch" if self.crouching else "idle")

        self.rect.left = max(bounds[0], self.rect.left)
        self.rect.right = min(bounds[1], self.rect.right)
        self.position_x = float(self.rect.x)

        if self.health <= 0:
            self._set_state("defeated")

        if self.blocking and self.state != "block":
            self.blocking = False

    def draw(self, surface):
        shadow_width = 86 if self.on_ground else 64
        shadow_height = 16 if self.on_ground else 10
        shadow = pygame.Surface((shadow_width, shadow_height), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 86 if self.on_ground else 52), shadow.get_rect())
        surface.blit(shadow, shadow.get_rect(center=(self.rect.centerx, self.rect.bottom + 6)))

        if self.sprite_frames:
            frame, outline = self._get_current_animation_frame()
            sprite_rect = frame.get_rect(midbottom=(self.rect.centerx, self.rect.bottom + 8))
            if self.state == "attack_light":
                sprite_rect.x += 10 * self.facing
            elif self.state == "attack_heavy":
                sprite_rect.x += 14 * self.facing
            elif self.state == "kick":
                sprite_rect.x += 12 * self.facing
            elif self.state == "low_kick":
                sprite_rect.x += 10 * self.facing
                sprite_rect.y += 4
            elif self.state == "flying_kick":
                sprite_rect.x += 18 * self.facing
                sprite_rect.y -= 10
            elif self.state == "dodge":
                sprite_rect.x += 8 * self.facing
            elif self.state == "defeated":
                sprite_rect.y += 18
            outline_rect = outline.get_rect(center=sprite_rect.center)
            for offset_x, offset_y in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                surface.blit(outline, outline_rect.move(offset_x, offset_y))
            surface.blit(frame, sprite_rect)
            if self.flash_timer > 0:
                flash = pygame.mask.from_surface(frame).to_surface(
                    setcolor=(255, 245, 230, int(190 * min(1.0, self.flash_timer / 0.08))),
                    unsetcolor=(0, 0, 0, 0),
                ).convert_alpha()
                surface.blit(flash, flash.get_rect(center=sprite_rect.center))
            return

        body = self.rect.copy()
        body.height = 110
        body.y += 22
        color = (120, 120, 130) if self.state == "defeated" else self.color
        pygame.draw.rect(surface, color, body, border_radius=8)
        sword = pygame.Rect(0, 0, 46, 8)
        sword.centery = body.centery
        sword.centerx = body.centerx + (34 * self.facing)
        pygame.draw.rect(surface, (200, 200, 210), sword)

    def _get_current_animation_frame(self):
        state = self.state if self.state in self.animation_frames else "idle"
        frames = self.flipped_animation_frames[state] if self.facing < 0 else self.animation_frames[state]
        outlines = self.flipped_animation_outlines[state] if self.facing < 0 else self.animation_outlines[state]
        if state in ATTACKS and self.attack_duration > 0:
            progress = min(0.999, max(0.0, (self.attack_duration - self.attack_timer) / self.attack_duration))
            index = int(progress * len(frames))
        elif state == "jump":
            if self.velocity_y < -220:
                index = 0
            elif self.velocity_y < 120:
                index = 1
            elif self.velocity_y < 420:
                index = 2
            else:
                index = 3
        elif state in {"hurt", "dodge", "landing"}:
            duration = self.hurt_timer if state == "hurt" else self.dodge_timer if state == "dodge" else self.landing_timer
            total = 0.30 if state == "hurt" else 0.32 if state == "dodge" else 0.10
            progress = min(0.999, max(0.0, 1.0 - duration / total))
            index = int(progress * len(frames))
        elif state == "defeated":
            index = len(frames) - 1
        else:
            speed = 9.5 if state == "walk" else 5.0 if state == "idle" else 7.0
            index = int(self.animation_time * speed) % len(frames)
        return frames[index], outlines[index]

    def _build_animation_bank(self):
        if len(self.sprite_frames) >= 10:
            frame_index = lambda index: max(0, min(len(self.sprite_frames) - 1, index))
            variants = {
                "idle": [(0, 1.00, 1.00, 0), (0, 1.01, 0.99, -1), (0, 1.00, 1.01, 0), (0, 0.99, 1.00, 1)],
                "walk": [(1, 0.99, 1.00, 0), (2, 1.01, 1.00, 0), (1, 1.00, 1.01, 0), (2, 1.00, 0.99, 0)],
                "attack_light": [(0, 0.98, 1.01, -2), (3, 0.96, 1.00, -2), (3, 1.01, 0.99, 0), (3, 1.03, 0.98, 1), (0, 1.00, 1.00, 0)],
                "attack_heavy": [(0, 0.96, 1.02, -4), (4, 0.92, 1.01, -3), (4, 0.98, 1.00, -1), (4, 1.05, 0.97, 2), (0, 1.00, 1.00, 0)],
                "kick": [(0, 0.98, 1.01, -2), (5, 0.97, 1.00, -2), (6, 1.00, 0.99, 0), (6, 1.02, 0.98, 1), (0, 1.00, 1.00, 0)],
                "low_kick": [(7, 1.00, 1.00, 0), (8, 0.99, 1.00, -1), (8, 1.02, 0.98, 0), (8, 1.01, 0.99, 1), (7, 1.00, 1.00, 0)],
                "flying_kick": [(5, 0.99, 1.00, 0), (6, 1.01, 0.99, 0), (6, 1.03, 0.98, 1), (5, 1.00, 1.00, 0)],
                "jump": [(5, 0.99, 1.01, -2), (5, 1.00, 1.00, 0), (6, 1.01, 0.99, 2), (5, 0.99, 1.00, 1)],
                "crouch": [(7, 1.00, 1.00, 0), (7, 1.01, 0.99, -1), (7, 1.00, 1.00, 0)],
                "hurt": [(9, 1.00, 1.00, 0), (9, 1.03, 0.97, 3), (9, 1.01, 0.99, 5), (9, 0.99, 1.01, 2)],
                "block": [(7, 1.00, 1.00, 0), (7, 1.02, 0.98, -1), (7, 1.00, 1.00, 0)],
                "dodge": [(5, 1.08, 0.92, -7), (6, 1.10, 0.90, -9), (5, 1.06, 0.94, -5), (0, 1.00, 1.00, 0)],
                "landing": [(7, 1.06, 0.94, 0), (7, 1.02, 0.98, 0), (0, 1.00, 1.00, 0)],
                "defeated": [(9, 1.00, 1.00, 78)],
            }
            for state, specs in variants.items():
                frames = [
                    self._make_variant(self.sprite_frames[frame_index(index)], scale_x, scale_y, angle)
                    for index, scale_x, scale_y, angle in specs
                ]
                self.animation_frames[state] = frames
                self.flipped_animation_frames[state] = [pygame.transform.flip(frame, True, False) for frame in frames]
                outlines = [self._build_outline(frame) for frame in frames]
                self.animation_outlines[state] = outlines
                self.flipped_animation_outlines[state] = [pygame.transform.flip(frame, True, False) for frame in outlines]
            return
        variants = {
            "idle": [(0, 1.00, 1.00, 0), (0, 1.01, 0.99, -1), (0, 1.00, 1.01, 0), (0, 0.99, 1.00, 1)],
            "walk": [(0, 0.98, 1.02, -2), (0, 1.00, 1.00, -1), (0, 1.02, 0.98, 1), (0, 1.00, 1.01, 2), (0, 0.98, 1.02, 1), (0, 1.01, 0.99, -1)],
            "attack_light": [(0, 0.98, 1.01, -3), (1, 0.94, 1.01, -2), (1, 1.00, 1.00, 0), (1, 1.04, 0.98, 2), (1, 1.01, 1.00, 1), (0, 1.00, 1.00, 0)],
            "attack_heavy": [(0, 0.96, 1.02, -5), (2, 0.91, 1.02, -4), (2, 0.97, 1.01, -2), (2, 1.04, 0.98, 1), (2, 1.07, 0.96, 3), (2, 1.01, 1.00, 1), (0, 1.00, 1.00, 0)],
            "kick": [(0, 0.97, 1.02, -3), (3, 0.93, 1.02, -3), (3, 1.00, 1.00, 0), (3, 1.07, 0.97, 2), (3, 1.02, 1.00, 1), (0, 1.00, 1.00, 0)],
            "jump": [(4, 0.98, 1.02, -3), (4, 1.00, 1.00, 0), (4, 1.02, 0.98, 3), (4, 0.98, 1.02, 5)],
            "crouch": [(5, 1.00, 1.00, 0), (5, 1.02, 0.98, -1), (5, 1.00, 1.00, 0)],
            "hurt": [(6, 1.00, 1.00, 0), (6, 1.04, 0.97, 4), (6, 1.01, 1.00, 7), (6, 0.99, 1.01, 3)],
            "block": [(5, 1.00, 1.00, 0), (5, 1.02, 0.98, -2), (5, 1.00, 1.00, 0)],
            "dodge": [(5, 1.08, 0.92, -8), (5, 1.12, 0.88, -10), (5, 1.08, 0.92, -7), (5, 1.02, 0.98, -3)],
            "landing": [(5, 1.08, 0.92, 0), (5, 1.03, 0.97, 0), (0, 1.00, 1.00, 0)],
            "defeated": [(6, 1.00, 1.00, 78)],
        }
        for state, specs in variants.items():
            frames = [self._make_variant(self.sprite_frames[index], scale_x, scale_y, angle) for index, scale_x, scale_y, angle in specs]
            self.animation_frames[state] = frames
            self.flipped_animation_frames[state] = [pygame.transform.flip(frame, True, False) for frame in frames]
            outlines = [self._build_outline(frame) for frame in frames]
            self.animation_outlines[state] = outlines
            self.flipped_animation_outlines[state] = [pygame.transform.flip(frame, True, False) for frame in outlines]

    def _make_variant(self, frame, scale_x, scale_y, angle):
        width = max(1, round(frame.get_width() * scale_x))
        height = max(1, round(frame.get_height() * scale_y))
        variant = pygame.transform.smoothscale(frame, (width, height))
        if angle:
            variant = pygame.transform.rotozoom(variant, angle, 1.0)
        return variant

    def _set_state(self, state):
        if self.state != state:
            self.state = state
            self.animation_state = state
            self.animation_time = 0.0

    def _sync_position_from_rect(self):
        self.position_x = float(self.rect.x)
        self.position_y = float(self.rect.y)

    @staticmethod
    def _approach(current, target, amount):
        if current < target:
            return min(target, current + amount)
        return max(target, current - amount)

    def _build_outline(self, frame):
        mask = pygame.mask.from_surface(frame)
        return mask.to_surface(
            setcolor=(*self.color, 120),
            unsetcolor=(0, 0, 0, 0),
        ).convert_alpha()
