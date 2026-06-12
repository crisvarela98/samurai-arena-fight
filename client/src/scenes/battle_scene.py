import json
from pathlib import Path

import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GREEN, LIGHT, GOLD, RED
from src.combat.ai_controller import AIController
from src.combat.combat_system import CombatSystem
from src.entities.fighter import Fighter, FighterStats
from src.entities.weapon import Weapon
from src.ui.desktop_controls import DesktopControls
from src.ui.health_bar import draw_bar, draw_portrait_badge
from src.ui.mobile_controls import MobileControls

class BattleScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.desktop_controls = DesktopControls()
        self.mobile_controls = MobileControls()
        self.ai = AIController()
        self.font = pygame.font.SysFont("arial", 24, bold=True)
        self.intro_font = pygame.font.SysFont("bahnschrift", 110, bold=True)
        self.intro_fight_font = pygame.font.SysFont("bahnschrift", 96, bold=True)
        self.intro_sequence = [("3", 0.65, LIGHT), ("2", 0.65, LIGHT), ("1", 0.65, LIGHT), ("FIGHT", 0.9, GOLD)]
        self.intro_timer = 0.0
        self.intro_total_duration = sum(duration for _, duration, _ in self.intro_sequence)
        self.current_intro_label = None
        self.setup_done = False

    def on_enter(self):
        self.setup_done = False
        self._build_match()
        self._reset_intro()

    def _reset_intro(self):
        self.intro_timer = 0.0
        self.current_intro_label = None
        self.game.input.clear_actions()

    def _spawn_positions(self, player_starts_left=True):
        screen_width = self.game.settings["screen_width"]
        margin = 84
        left_x = margin
        right_x = screen_width - margin - 72
        return (left_x, right_x) if player_starts_left else (right_x, left_x)

    def _intro_active(self):
        return self.intro_timer < self.intro_total_duration

    def _update_intro(self, dt):
        self.intro_timer = min(self.intro_total_duration, self.intro_timer + dt)
        self.game.input.clear_actions()
        self.player.velocity_x = 0
        self.player.velocity_y = 0
        self.enemy.velocity_x = 0
        self.enemy.velocity_y = 0
        if self.player.health > 0:
            self.player.state = "idle"
        if self.enemy.health > 0:
            self.enemy.state = "idle"
        label, _ = self._current_intro_text()
        if label and label != self.current_intro_label:
            if label == "FIGHT":
                self.game.audio.play_fight()
            else:
                self.game.audio.play_count_tick()
            self.current_intro_label = label

    def _current_intro_text(self):
        elapsed = 0.0
        for label, duration, color in self.intro_sequence:
            elapsed += duration
            if self.intro_timer < elapsed:
                return label, color
        return None, LIGHT

    def _draw_intro_overlay(self, surface):
        if not self._intro_active():
            return
        label, color = self._current_intro_text()
        if not label:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 68))
        surface.blit(overlay, (0, 0))
        font = self.intro_fight_font if label == "FIGHT" else self.intro_font
        text = font.render(label, True, color if label != "FIGHT" else GREEN)
        shadow = font.render(label, True, (0, 0, 0))
        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2 - 10
        shadow_rect = shadow.get_rect(center=(center_x + 4, center_y + 4))
        text_rect = text.get_rect(center=(center_x, center_y))
        surface.blit(shadow, shadow_rect)
        surface.blit(text, text_rect)

    def _build_match(self):
        root = Path(__file__).resolve().parents[2]
        fighters = json.loads((root / "data" / "fighters.json").read_text(encoding="utf-8"))
        weapons = json.loads((root / "data" / "weapons.json").read_text(encoding="utf-8"))
        arenas = json.loads((root / "data" / "arenas.json").read_text(encoding="utf-8"))
        fighter_a = next(item for item in fighters if item["id"] == self.game.shared["selected_fighter"])
        fighter_b = next(item for item in fighters if item["id"] != fighter_a["id"])
        weapon_map = {item["id"]: item for item in weapons}
        arena = next(item for item in arenas if item["id"] == self.game.shared["selected_arena"])
        player_x, enemy_x = self._spawn_positions(player_starts_left=True)
        self.player = Fighter(FighterStats(**fighter_a), Weapon(**weapon_map[fighter_a["weapon_id"]]), player_x, arena["floor_y"] - 132, (180, 55, 55), self.game.assets)
        self.enemy = Fighter(FighterStats(**fighter_b), Weapon(**weapon_map[fighter_b["weapon_id"]]), enemy_x, arena["floor_y"] - 132, (55, 100, 160), self.game.assets)
        self.enemy.facing = -1
        self.combat = CombatSystem(self.player, self.enemy, arena, audio=self.game.audio)
        self.arena = arena
        self.background_image = None
        self.floor_image = None
        screen_width = self.game.settings["screen_width"]
        screen_height = self.game.settings["screen_height"]
        floor_top = max(0, arena["floor_y"] - 18)
        if arena.get("background"):
            self.background_image = self.game.assets.load_image(
                arena["background"],
                size=(screen_width, screen_height),
            )
        if arena.get("floor"):
            self.floor_image = self.game.assets.load_image(
                arena["floor"],
                size=(screen_width, screen_height - floor_top),
                trim_alpha=True,
                chroma_key=(0, 255, 0),
                chroma_tolerance=84,
            )
            self.floor_top = floor_top
        else:
            self.floor_top = arena["floor_y"]
        self.paused = False
        self.result = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.scene_manager.push(self.game.scenes["pause"])
        if self.game.shared["selected_platform"] == "android" and event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP}:
            action = self.mobile_controls.action_from_pos(event.pos)
            if action:
                pressed = event.type == pygame.MOUSEBUTTONDOWN
                if self._intro_active() and action != "pause":
                    return
                if action == "left":
                    self.game.input.set_action("left", pressed)
                elif action == "right":
                    self.game.input.set_action("right", pressed)
                elif action == "up":
                    self.game.input.set_action("up", pressed)
                elif action == "down":
                    self.game.input.set_action("down", pressed)
                elif action == "light" and pressed:
                    self.player.start_attack("attack_light")
                elif action == "heavy" and pressed:
                    self.player.start_attack("attack_heavy")
                elif action == "kick" and pressed:
                    self.player.start_attack("kick")
                elif action == "block":
                    self.player.block(pressed)
                elif action == "dodge" and pressed:
                    self.player.dodge()
                elif action == "pause" and pressed:
                    self.game.go("pause")

    def update(self, dt):
        if self._intro_active():
            self._update_intro(dt)
            return
        self.player.crouch(self.game.input.is_down("down"))
        if self.player.crouching:
            self.player.move(0, dt)
        elif self.game.input.is_down("left"):
            self.player.move(-1, dt)
        elif self.game.input.is_down("right"):
            self.player.move(1, dt)
        else:
            self.player.move(0, dt)
        if self.game.input.was_pressed("up"):
            self.player.jump()
        if self.game.input.was_pressed("light"):
            self.player.start_attack("attack_light")
        if self.game.input.was_pressed("heavy"):
            self.player.start_attack("attack_heavy")
        if self.game.input.was_pressed("kick"):
            self.player.start_attack("kick")
        self.player.block(self.game.input.is_down("block"))
        if self.game.input.was_pressed("dodge"):
            self.player.dodge()
        ai_actions = self.ai.update(self.enemy, self.player, dt)
        self.enemy.move((-1 if ai_actions["left"] else 1 if ai_actions["right"] else 0), dt)
        if ai_actions["light"]:
            self.enemy.start_attack("attack_light")
        if ai_actions["heavy"]:
            self.enemy.start_attack("attack_heavy")
        if ai_actions["block"]:
            self.enemy.block(True)
        else:
            self.enemy.block(False)
        if ai_actions["dodge"]:
            self.enemy.dodge()
        self.combat.update(dt)
        if self.combat.round_finished:
            self.game.shared["result"] = "victory" if self.combat.winner is self.player else "defeat"
            self.game.go("result")

    def draw(self, surface):
        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        else:
            surface.fill((10, 10, 12))
            pygame.draw.rect(surface, (28, 20, 20), (0, 0, 1280, 720))
        if self.floor_image:
            surface.blit(self.floor_image, (0, self.floor_top))
        else:
            pygame.draw.rect(surface, (30, 30, 34), (0, self.arena["floor_y"], 1280, 160))
            pygame.draw.rect(surface, (90, 70, 50), (0, self.arena["floor_y"], 1280, 6))
        self.player.draw(surface)
        self.enemy.draw(surface)

        draw_portrait_badge(surface, pygame.Rect(34, 18, 96, 96), self.player.portrait_image, accent=(180, 85, 75))
        draw_portrait_badge(surface, pygame.Rect(1150, 18, 96, 96), self.enemy.portrait_image, accent=(75, 120, 190), flip=True)
        draw_bar(surface, 144, 30, 430, 24, self.player.health, self.player.stats.max_health, self.player.stats.name.upper())
        draw_bar(surface, 706, 30, 430, 24, self.enemy.health, self.enemy.stats.max_health, self.enemy.stats.name.upper())
        draw_bar(surface, 144, 68, 300, 18, self.player.stamina, self.player.stats.max_stamina, "STAMINA")
        draw_bar(surface, 836, 68, 300, 18, self.enemy.stamina, self.enemy.stats.max_stamina, "STAMINA")
        round_text = self.font.render("COMBATE", True, LIGHT)
        surface.blit(round_text, round_text.get_rect(center=(640, 20)))
        if self.game.shared["selected_platform"] == "android":
            self.mobile_controls.draw(surface)
        else:
            self.desktop_controls.draw_hint(surface)
        self._draw_intro_overlay(surface)
