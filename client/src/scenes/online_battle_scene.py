import json
from pathlib import Path

import pygame

from src.combat.moves import ATTACKS
from src.core.constants import LIGHT
from src.entities.fighter import Fighter, FighterStats
from src.entities.weapon import Weapon
from src.core.input_manager import DESKTOP_HINT_TEXT
from src.scenes.battle_scene import BattleScene
from src.ui.health_bar import draw_bar, draw_portrait_badge


class OnlineBattleScene(BattleScene):
    def __init__(self, game):
        super().__init__(game)
        self.net = self.game.network
        self.remote_actions = {"left": False, "right": False, "down": False}
        self.remote_jump_requested = False
        self.last_sent_axes = {"left": False, "right": False, "down": False}
        self.last_sent_block = False
        self.player_meta = {}
        self.enemy_meta = {}
        self.player_starts_left = True

    def on_enter(self):
        self.net = self.game.network
        self.remote_actions = {"left": False, "right": False, "down": False}
        self.remote_jump_requested = False
        self.last_sent_axes = {"left": False, "right": False, "down": False}
        self.last_sent_block = False
        self.game.shared["online_battle_exit"] = False
        self._bind_network_callbacks()
        self._build_match()
        self._reset_intro()

    def _bind_network_callbacks(self):
        self.net.on("opponent_input", self._on_opponent_input)
        self.net.on("opponent_attack", self._on_opponent_attack)
        self.net.on("opponent_block", self._on_opponent_block)
        self.net.on("opponent_dodge", self._on_opponent_dodge)
        self.net.on("fighter_hit", self._on_fighter_hit)
        self.net.on("health_update", self._on_health_update)
        self.net.on("match_finished", self._on_match_finished)
        self.net.on("opponent_left", self._on_opponent_left)
        self.net.on("error_message", self._on_error)

    def _build_match(self):
        root = Path(__file__).resolve().parents[2]
        fighters = json.loads((root / "data" / "fighters.json").read_text(encoding="utf-8"))
        weapons = json.loads((root / "data" / "weapons.json").read_text(encoding="utf-8"))
        arenas = json.loads((root / "data" / "arenas.json").read_text(encoding="utf-8"))

        match_data = self.game.shared.get("online_match_data") or {}
        players = match_data.get("players") or []
        local_socket_id = self.net.state.socket_id
        self.player_meta = next((player for player in players if player.get("socketId") == local_socket_id), None) or {}
        self.enemy_meta = next((player for player in players if player.get("socketId") != local_socket_id), None) or {}

        if not self.player_meta and players:
            role = self.game.shared.get("online_role")
            self.player_meta = players[1] if role == "guest" and len(players) > 1 else players[0]
            self.enemy_meta = next((player for player in players if player != self.player_meta), {})

        if not self.player_meta:
            self.player_meta = {
                "username": self.game.shared.get("online_username", "player"),
                "platform": self.game.shared.get("selected_platform", "pc"),
                "fighterId": self.game.shared["selected_fighter"],
                "arenaId": self.game.shared["selected_arena"],
                "socketId": local_socket_id,
                "health": 100,
                "stamina": 100,
            }
        if not self.enemy_meta:
            fallback_enemy = next((fighter for fighter in fighters if fighter["id"] != self.player_meta.get("fighterId")), fighters[0])
            self.enemy_meta = {
                "username": "rival",
                "platform": "pc",
                "fighterId": fallback_enemy["id"],
                "arenaId": self.player_meta.get("arenaId", self.game.shared["selected_arena"]),
                "socketId": None,
                "health": 100,
                "stamina": 100,
            }

        arena_id = match_data.get("arenaId") or self.player_meta.get("arenaId") or self.game.shared["selected_arena"]
        arena = next(item for item in arenas if item["id"] == arena_id)
        weapon_map = {item["id"]: item for item in weapons}
        fighter_map = {item["id"]: item for item in fighters}

        local_data = fighter_map[self.player_meta["fighterId"]]
        enemy_data = fighter_map[self.enemy_meta["fighterId"]]

        if players:
            first_socket_id = players[0].get("socketId")
            self.player_starts_left = first_socket_id == self.player_meta.get("socketId")
        else:
            self.player_starts_left = self.game.shared.get("online_role") != "guest"

        player_x, enemy_x = self._spawn_positions(player_starts_left=self.player_starts_left)
        self.player = Fighter(FighterStats(**local_data), Weapon(**weapon_map[local_data["weapon_id"]]), player_x, arena["floor_y"] - 132, (180, 55, 55), self.game.assets)
        self.enemy = Fighter(FighterStats(**enemy_data), Weapon(**weapon_map[enemy_data["weapon_id"]]), enemy_x, arena["floor_y"] - 132, (55, 100, 160), self.game.assets)
        self.player.facing = 1 if self.player_starts_left else -1
        self.enemy.facing = -1 if self.player_starts_left else 1
        self.player.health = self.player_meta.get("health", self.player.health)
        self.enemy.health = self.enemy_meta.get("health", self.enemy.health)
        self.arena = arena
        self._load_arena_art()

    def _load_arena_art(self):
        self.background_image = None
        self.floor_image = None
        screen_width = self.game.settings["screen_width"]
        screen_height = self.game.settings["screen_height"]
        floor_top = max(0, self.arena["floor_y"] - 18)
        if self.arena.get("background"):
            self.background_image = self.game.assets.load_image(
                self.arena["background"],
                size=(screen_width, screen_height),
            )
        if self.arena.get("floor"):
            self.floor_image = self.game.assets.load_image(
                self.arena["floor"],
                size=(screen_width, screen_height - floor_top),
                trim_alpha=True,
                chroma_key=(0, 255, 0),
                chroma_tolerance=84,
            )
            self.floor_top = floor_top
        else:
            self.floor_top = self.arena["floor_y"]

    def _queue_result(self, result):
        self.game.shared["result"] = result
        self.game.shared["online_battle_exit"] = True

    def _leave_match(self, result_message="Abandonaste la partida"):
        try:
            self.net.leave_room()
        except Exception:
            pass
        self._queue_result(result_message)

    def _on_opponent_input(self, data):
        if self._intro_active():
            return
        self.remote_actions["left"] = bool(data.get("left"))
        self.remote_actions["right"] = bool(data.get("right"))
        self.remote_actions["down"] = bool(data.get("down"))
        if data.get("jump"):
            self.remote_jump_requested = True

    def _on_opponent_attack(self, data):
        if self._intro_active():
            return
        attack_type = data.get("attackType")
        if attack_type in ATTACKS:
            self.enemy.start_attack(attack_type)

    def _on_opponent_block(self, data):
        if self._intro_active():
            return
        self.enemy.block(bool(data.get("active")))

    def _on_opponent_dodge(self, data):
        if self._intro_active():
            return
        self.enemy.dodge()

    def _on_fighter_hit(self, data):
        if self._intro_active():
            return
        defender_socket_id = data.get("defenderSocketId")
        target = None
        if defender_socket_id == self.player_meta.get("socketId"):
            target = self.player
        elif defender_socket_id == self.enemy_meta.get("socketId"):
            target = self.enemy
        if target:
            if target is self.player:
                self.game.audio.play_hit(data.get("attackType"))
            target.apply_network_hit(int(data.get("damage", 0)), int(data.get("knockback", 0)))
            if "defenderHealth" in data:
                target.health = data.get("defenderHealth", target.health)
                if target.health <= 0:
                    target.state = "defeated"

    def _on_health_update(self, data):
        for player in data.get("players", []):
            socket_id = player.get("socketId")
            if socket_id == self.player_meta.get("socketId"):
                self.player.health = player.get("health", self.player.health)
                self.player.stamina = player.get("stamina", self.player.stamina)
            elif socket_id == self.enemy_meta.get("socketId"):
                self.enemy.health = player.get("health", self.enemy.health)
                self.enemy.stamina = player.get("stamina", self.enemy.stamina)

    def _on_match_finished(self, data):
        winner_socket_id = data.get("winnerSocketId")
        if winner_socket_id and winner_socket_id == self.player_meta.get("socketId"):
            self._queue_result("victory")
        elif winner_socket_id and winner_socket_id == self.enemy_meta.get("socketId"):
            self._queue_result("defeat")
        else:
            self._queue_result(data.get("winner", "resultado"))

    def _on_opponent_left(self, data):
        self._queue_result(data.get("message", "El rival salio"))

    def _on_error(self, data):
        self._queue_result(data.get("message", "Error online"))

    def _send_axes(self, jump_pressed=False):
        if self._intro_active():
            return
        current_axes = {
            "left": self.game.input.is_down("left"),
            "right": self.game.input.is_down("right"),
            "down": self.game.input.is_down("down"),
        }
        if current_axes != self.last_sent_axes or jump_pressed:
            payload = dict(current_axes)
            payload["jump"] = jump_pressed
            self.net.send_input(payload)
            self.last_sent_axes = current_axes

    def _resolve_overlap(self):
        if self.player.rect.colliderect(self.enemy.rect):
            overlap = self.player.rect.centerx - self.enemy.rect.centerx
            push = 1 if overlap < 0 else -1
            self.player.rect.x += push * 2
            self.enemy.rect.x -= push * 2

    def _resolve_local_hits(self):
        if self.player.state not in ATTACKS:
            return
        info = ATTACKS[self.player.state]
        hit_rect = self.player.hitbox.rect.inflate(info["range"] - self.player.hitbox.width, 8)
        if not hit_rect.colliderect(self.enemy.rect):
            return
        damage = info["damage"] + self.player.stats.attack_power // 5
        knockback = info["knockback"]
        blocked = self.enemy.blocking
        if blocked:
            damage = max(1, int(damage * 0.35))
            knockback = int(knockback * 0.45)
        self.net.send_hit(
            {
                "attackType": self.player.state,
                "damage": damage,
                "health": max(0, self.enemy.health - damage),
                "knockback": knockback * self.player.facing,
                "blocked": blocked,
            }
        )
        self.game.audio.play_hit(self.player.state)
        self.player.state = "idle"

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._leave_match()
            return
        if self.game.shared["selected_platform"] == "android" and event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP}:
            action = self.mobile_controls.action_from_pos(event.pos)
            if action:
                pressed = event.type == pygame.MOUSEBUTTONDOWN
                if self._intro_active() and action != "pause":
                    return
                if action in {"left", "right", "up", "down", "block"}:
                    self.game.input.set_action(action, pressed)
                elif action == "light" and pressed:
                    if self.player.start_attack("attack_light"):
                        self.net.send_attack("attack_light")
                elif action == "heavy" and pressed:
                    if self.player.start_attack("attack_heavy"):
                        self.net.send_attack("attack_heavy")
                elif action == "kick" and pressed:
                    if self.player.start_attack("kick"):
                        self.net.send_attack("kick")
                elif action == "dodge" and pressed:
                    if self.player.dodge():
                        self.net.send_dodge()
                elif action == "pause" and pressed:
                    self._leave_match()

    def update(self, dt):
        if self.game.shared.get("online_battle_exit"):
            self.game.shared["online_battle_exit"] = False
            self.game.go("result")
            return
        if self._intro_active():
            self.remote_actions = {"left": False, "right": False, "down": False}
            self.remote_jump_requested = False
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

        jump_pressed = self.game.input.was_pressed("up") and self.player.jump()
        self._send_axes(jump_pressed=jump_pressed)

        if self.game.input.was_pressed("light") and self.player.start_attack("attack_light"):
            self.net.send_attack("attack_light")
        if self.game.input.was_pressed("heavy") and self.player.start_attack("attack_heavy"):
            self.net.send_attack("attack_heavy")
        if self.game.input.was_pressed("kick") and self.player.start_attack("kick"):
            self.net.send_attack("kick")

        block_active = self.game.input.is_down("block")
        self.player.block(block_active)
        if block_active != self.last_sent_block:
            self.net.send_block(block_active)
            self.last_sent_block = block_active

        if self.game.input.was_pressed("dodge") and self.player.dodge():
            self.net.send_dodge()

        self.enemy.crouch(self.remote_actions["down"])
        if self.remote_jump_requested:
            self.enemy.jump()
            self.remote_jump_requested = False
        if self.enemy.crouching:
            self.enemy.move(0, dt)
        elif self.remote_actions["left"]:
            self.enemy.move(-1, dt)
        elif self.remote_actions["right"]:
            self.enemy.move(1, dt)
        else:
            self.enemy.move(0, dt)

        self.player.update(dt, self.arena["floor_y"], (0, 1280))
        self.enemy.update(dt, self.arena["floor_y"], (0, 1280))
        self._resolve_overlap()
        self._resolve_local_hits()

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

        left_fighter = self.player if self.player_starts_left else self.enemy
        right_fighter = self.enemy if self.player_starts_left else self.player
        left_name = self.player_meta.get("username", "player") if self.player_starts_left else self.enemy_meta.get("username", "rival")
        right_name = self.enemy_meta.get("username", "rival") if self.player_starts_left else self.player_meta.get("username", "player")

        draw_portrait_badge(surface, pygame.Rect(34, 18, 96, 96), left_fighter.portrait_image, accent=(180, 85, 75), flip=not self.player_starts_left)
        draw_portrait_badge(surface, pygame.Rect(1150, 18, 96, 96), right_fighter.portrait_image, accent=(75, 120, 190), flip=self.player_starts_left)
        draw_bar(surface, 144, 30, 430, 24, left_fighter.health, left_fighter.stats.max_health, left_name.upper())
        draw_bar(surface, 706, 30, 430, 24, right_fighter.health, right_fighter.stats.max_health, right_name.upper())
        draw_bar(surface, 144, 68, 300, 18, left_fighter.stamina, left_fighter.stats.max_stamina, "STAMINA")
        draw_bar(surface, 836, 68, 300, 18, right_fighter.stamina, right_fighter.stats.max_stamina, "STAMINA")

        name_font = pygame.font.SysFont("bahnschrift", 16, bold=True)
        left_fighter_name = name_font.render(left_fighter.stats.name.upper(), True, LIGHT)
        right_fighter_name = name_font.render(right_fighter.stats.name.upper(), True, LIGHT)
        surface.blit(left_fighter_name, (144, 92))
        surface.blit(right_fighter_name, (1136 - right_fighter_name.get_width(), 92))

        round_text = self.font.render("COMBATE ONLINE", True, LIGHT)
        surface.blit(round_text, round_text.get_rect(center=(640, 20)))
        room_text = pygame.font.SysFont("arial", 18, bold=True).render(
            f"SALA {self.game.shared.get('online_room', '---')}",
            True,
            LIGHT,
        )
        surface.blit(room_text, room_text.get_rect(center=(640, 52)))

        if self.game.shared["selected_platform"] == "android":
            self.mobile_controls.draw(surface)
        else:
            hint_font = pygame.font.SysFont("arial", 18)
            surface.blit(hint_font.render(DESKTOP_HINT_TEXT, True, LIGHT), (20, 688))
        self._draw_intro_overlay(surface)
