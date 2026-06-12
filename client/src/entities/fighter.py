from dataclasses import dataclass

import pygame

from src.entities.hitbox import Hitbox


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


class Fighter:
    def __init__(self, stats, weapon, x, y, color, asset_loader=None):
        self.stats = stats
        self.weapon = weapon
        self.rect = pygame.Rect(x, y, 72, 132)
        self.color = color
        self.facing = 1
        self.velocity_x = 0
        self.velocity_y = 0
        self.on_ground = True
        self.health = stats.max_health
        self.stamina = stats.max_stamina
        self.state = "idle"
        self.attack_timer = 0.0
        self.cooldown_timer = 0.0
        self.blocking = False
        self.crouching = False
        self.invincible_timer = 0.0
        self.hurt_timer = 0.0
        self.dodge_timer = 0.0
        self.combo_damage = 0
        self.hitbox = Hitbox(self, 50, 28, 52, 40)
        self.sprite_frames = []
        self.flipped_frames = []
        self.outline_frames = []
        self.flipped_outline_frames = []
        self.portrait_image = None
        if asset_loader and stats.sprite_sheet:
            self.sprite_frames = asset_loader.load_sprite_strip(
                stats.sprite_sheet,
                7,
                scale_height=180,
                chroma_key=(0, 255, 0),
                chroma_tolerance=92,
                despill=True,
            )
            self.flipped_frames = [pygame.transform.flip(frame, True, False) for frame in self.sprite_frames]
            self.outline_frames = [self._build_outline(frame) for frame in self.sprite_frames]
            self.flipped_outline_frames = [pygame.transform.flip(frame, True, False) for frame in self.outline_frames]
        if asset_loader and stats.portrait:
            self.portrait_image = asset_loader.load_image(
                stats.portrait,
                trim_alpha=True,
            )

    def move(self, direction, dt):
        if self.state in {"attack_light", "attack_heavy", "kick", "hurt", "dodge", "defeated"} or self.crouching:
            self.velocity_x = 0
            return
        self.velocity_x = direction * self.stats.speed
        if direction:
            self.facing = 1 if direction > 0 else -1
            self.state = "walk"
        elif not self.blocking:
            self.state = "idle"

    def jump(self):
        if self.on_ground and self.state not in {"dodge", "hurt", "defeated"}:
            self.crouching = False
            self.velocity_y = -560
            self.on_ground = False
            self.state = "jump"
            return True
        return False

    def crouch(self, active):
        self.crouching = active and self.on_ground and self.state not in {
            "attack_light",
            "attack_heavy",
            "kick",
            "hurt",
            "dodge",
            "defeated",
        }
        if self.crouching:
            self.velocity_x = 0
            self.state = "crouch"
        elif self.state == "crouch":
            self.state = "idle"

    def start_attack(self, attack_name):
        if self.cooldown_timer > 0 or self.stamina <= 0 or self.state in {"hurt", "dodge", "defeated"}:
            return False
        self.crouching = False
        self.state = attack_name
        self.attack_timer = 0.22 if attack_name == "attack_light" else 0.34 if attack_name == "attack_heavy" else 0.25
        self.cooldown_timer = self.weapon.cooldown
        self.stamina = max(0, self.stamina - self.weapon.stamina_cost)
        return True

    def block(self, active):
        if active:
            self.crouching = False
        self.blocking = active and self.state not in {"attack_light", "attack_heavy", "kick", "dodge", "defeated"}
        if self.blocking:
            self.state = "block"

    def dodge(self):
        if self.stamina < 18 or self.state in {"hurt", "dodge", "defeated"}:
            return False
        self.crouching = False
        self.state = "dodge"
        self.dodge_timer = 0.28
        self.invincible_timer = 0.28
        self.stamina -= 18
        self.velocity_x = 260 * self.facing
        return True

    def take_damage(self, amount, knockback):
        if self.invincible_timer > 0 or self.state == "defeated":
            return 0
        if self.blocking:
            amount = max(1, int(amount * 0.35))
            knockback = int(knockback * 0.45)
        self.crouching = False
        self.health = max(0, self.health - amount)
        self.state = "hurt"
        self.hurt_timer = 0.22
        self.velocity_x += knockback * self.facing
        return amount

    def apply_network_hit(self, damage, knockback):
        if self.state == "defeated":
            return
        self.crouching = False
        self.blocking = False
        self.health = max(0, self.health - damage)
        if self.health <= 0:
            self.state = "defeated"
            self.hurt_timer = 0.0
        else:
            self.state = "hurt"
            self.hurt_timer = 0.22
        self.velocity_x += knockback

    def update(self, dt, floor_y, bounds):
        if self.cooldown_timer > 0:
            self.cooldown_timer = max(0, self.cooldown_timer - dt)
        if self.invincible_timer > 0:
            self.invincible_timer = max(0, self.invincible_timer - dt)
        if self.hurt_timer > 0:
            self.hurt_timer = max(0, self.hurt_timer - dt)
            if self.hurt_timer == 0 and self.health > 0:
                self.state = "idle"
        if self.dodge_timer > 0:
            self.dodge_timer = max(0, self.dodge_timer - dt)
            if self.dodge_timer == 0 and self.health > 0:
                self.state = "idle"
        if self.attack_timer > 0:
            self.attack_timer = max(0, self.attack_timer - dt)
            if self.attack_timer == 0 and self.health > 0:
                self.state = "idle"

        self.velocity_y += 1600 * dt
        self.rect.x += int(self.velocity_x * dt)
        self.rect.y += int(self.velocity_y * dt)

        self.velocity_x *= 0.82
        if abs(self.velocity_x) < 4:
            self.velocity_x = 0

        if self.rect.bottom >= floor_y:
            self.rect.bottom = floor_y
            self.velocity_y = 0
            self.on_ground = True
        else:
            self.on_ground = False

        if not self.on_ground and self.state not in {"attack_light", "attack_heavy", "kick", "hurt", "dodge", "defeated"}:
            self.state = "jump"
            self.crouching = False
        elif self.on_ground and self.state == "jump":
            self.state = "crouch" if self.crouching else "idle"

        self.rect.left = max(bounds[0], self.rect.left)
        self.rect.right = min(bounds[1], self.rect.right)

        if self.health <= 0:
            self.state = "defeated"

        if self.blocking and self.state != "block":
            self.blocking = False

    def draw(self, surface):
        shadow_width = 86 if self.on_ground else 64
        shadow_height = 16 if self.on_ground else 10
        shadow = pygame.Surface((shadow_width, shadow_height), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 86 if self.on_ground else 52), shadow.get_rect())
        surface.blit(shadow, shadow.get_rect(center=(self.rect.centerx, self.rect.bottom + 6)))

        if self.sprite_frames:
            frame_index = self._get_current_frame_index()
            frame = self.flipped_frames[frame_index] if self.facing < 0 else self.sprite_frames[frame_index]
            outline = self.flipped_outline_frames[frame_index] if self.facing < 0 else self.outline_frames[frame_index]
            sprite_rect = frame.get_rect(midbottom=(self.rect.centerx, self.rect.bottom + 8))
            if self.state == "attack_light":
                sprite_rect.x += 10 * self.facing
            elif self.state == "attack_heavy":
                sprite_rect.x += 14 * self.facing
            elif self.state == "kick":
                sprite_rect.x += 12 * self.facing
            outline_rect = outline.get_rect(center=sprite_rect.center)
            for offset_x, offset_y in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                surface.blit(outline, outline_rect.move(offset_x, offset_y))
            surface.blit(frame, sprite_rect)
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

    def _get_current_frame(self):
        return self.sprite_frames[self._get_current_frame_index()]

    def _get_current_frame_index(self):
        if self.state == "attack_light":
            return 1
        if self.state == "attack_heavy":
            return 2
        if self.state == "kick":
            return 3
        if self.state == "jump":
            return 4
        if self.state == "crouch":
            return 5
        if self.state == "hurt":
            return 6
        return 0

    def _build_outline(self, frame):
        mask = pygame.mask.from_surface(frame)
        return mask.to_surface(
            setcolor=(*self.color, 120),
            unsetcolor=(0, 0, 0, 0),
        ).convert_alpha()
