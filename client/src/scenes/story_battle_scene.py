import json
from pathlib import Path

import pygame

from src.combat.ai_controller import AIController
from src.combat.combat_system import CombatSystem
from src.core.constants import GOLD, GREEN, LIGHT, RED
from src.entities.fighter import Fighter, FighterStats
from src.entities.weapon import Weapon
from src.scenes.battle_scene import BattleScene
from src.ui.menu_theme import draw_chip, draw_panel, get_font


class _StoryAI:
    def __init__(self):
        self.controller = AIController()
        self.active = True

    def update(self, fighter, opponent, dt):
        if self.active:
            return self.controller.update(fighter, opponent, dt)
        return {"left": False, "right": False, "light": False, "heavy": False, "kick": False, "block": False, "dodge": False}


class StoryBattleScene(BattleScene):
    ROUNDS_TO_WIN = 1
    ROUND_RESET_DELAY = 1.2
    FTUE_STEPS = [
        {"title": "LEVANTATE", "detail": "Usa A/D o los botones IZQ/DER.", "action": "move", "deadline": 31},
        {"title": "ACERCATE", "detail": "Algo se mueve entre los cuerpos. Reduce la distancia.", "action": "approach", "deadline": 42},
        {"title": "SOLDADO HERIDO", "detail": '"Esa espada... Tu eres el Demonio de Acero."', "action": "narrative", "deadline": 45},
        {"title": "EL CUERPO RECUERDA", "detail": "Ataque rapido: J o boton GOLPE.", "action": "light", "deadline": 58},
        {"title": "ROMPE SU GUARDIA", "detail": "Ataque fuerte: K o boton SUPER.", "action": "heavy", "deadline": 69},
        {"title": "CONTROLA TU FUERZA", "detail": "Los ataques consumen stamina; deja que se regenere.", "action": "stamina", "deadline": 75},
        {"title": "PROTEGETE", "detail": "Mantiene I o el boton BLOQUEO.", "action": "block", "deadline": 86},
        {"title": "SAL DE LA LINEA", "detail": "Usa O o el boton ESQUIVA.", "action": "dodge", "deadline": 96},
        {"title": "SOBREVIVE", "detail": "Derrota al soldado antes de que lleguen los demas.", "action": "combat", "deadline": 108},
    ]

    def __init__(self, game):
        super().__init__(game)
        root = Path(__file__).resolve().parents[2]
        self.missions = json.loads((root / "data" / "story" / "missions.json").read_text(encoding="utf-8"))
        enemies = json.loads((root / "data" / "story" / "enemies.json").read_text(encoding="utf-8"))
        self.enemies = {item["id"]: item for item in enemies}
        self.kenji_data = json.loads((root / "data" / "story" / "story_fighter.json").read_text(encoding="utf-8"))
        self.story_ai = _StoryAI()
        self.ai = self.story_ai
        self.ftue_step = 0
        self.ftue_step_elapsed = 0.0
        self.ftue_actions_seen = set()

    def _mission(self):
        number = int(self.game.shared.get("story_mission", 1))
        return next(item for item in self.missions if item["number"] == number)

    def on_enter(self):
        self.ftue_step = 0
        self.ftue_step_elapsed = 0.0
        self.ftue_actions_seen = set()
        self.story_ai = _StoryAI()
        self.ai = self.story_ai
        self.story_ai.active = not self._mission().get("ftue", False)
        if self._mission().get("ftue"):
            self.game.shared.setdefault("story_episode_elapsed", 0.0)
            self.game.shared["story_episode_active"] = True
        super().on_enter()

    def handle_event(self, event):
        if self._mission().get("ftue") and self.game.shared["selected_platform"] == "android" and event.type == pygame.MOUSEBUTTONDOWN:
            action = self.mobile_controls.action_from_pos(event.pos)
            if action:
                self.ftue_actions_seen.add(action)
        super().handle_event(event)

    def _build_match(self):
        root = Path(__file__).resolve().parents[2]
        weapons = json.loads((root / "data" / "weapons.json").read_text(encoding="utf-8"))
        arenas = json.loads((root / "data" / "arenas.json").read_text(encoding="utf-8"))
        weapon_map = {item["id"]: item for item in weapons}
        mission = self._mission()
        fight_index = int(self.game.shared.get("story_fight_index", 0))
        enemy_data = self.enemies[mission["fights"][fight_index]]
        arena = next(item for item in arenas if item["id"] == mission["arena_id"])
        player_x, enemy_x = self._spawn_positions(True)
        fighter_fields = FighterStats.__dataclass_fields__
        kenji_stats = {key: value for key, value in self.kenji_data.items() if key in fighter_fields}
        self.player = Fighter(FighterStats(**kenji_stats), Weapon(**weapon_map[self.kenji_data["weapon_id"]]), player_x, arena["floor_y"] - 132, (180, 55, 55), self.game.assets)
        enemy_stats = {key: value for key, value in enemy_data.items() if key != "ai_level"}
        self.enemy = Fighter(FighterStats(**enemy_stats), Weapon(**weapon_map[enemy_data["weapon_id"]]), enemy_x, arena["floor_y"] - 132, (55, 100, 160), self.game.assets)
        self.enemy.facing = -1
        self.combat = CombatSystem(self.player, self.enemy, arena, audio=self.game.audio)
        self.arena = arena
        self.background_image = self.game.assets.load_image(arena["background"], size=(1280, 720))
        self.floor_top = max(0, arena["floor_y"] - 18)
        self.floor_image = self.game.assets.load_image(
            arena["floor"], size=(1280, 720 - self.floor_top), trim_alpha=True,
            chroma_key=(0, 255, 0), chroma_tolerance=84,
        )
        self.paused = False
        self.result = None

    def _build_intro_sequence(self):
        mission = self._mission()
        fight_number = int(self.game.shared.get("story_fight_index", 0)) + 1
        return [
            (f"ROUND {fight_number}", 1.15, GOLD),
            ("3", 0.5, LIGHT), ("2", 0.5, LIGHT), ("1", 0.5, LIGHT), ("FIGHT", 0.75, GOLD),
        ]

    def _finalize_match(self, player_won):
        mission = self._mission()
        if not player_won:
            if mission.get("ftue"):
                self.game.shared["story_episode_active"] = False
            self.game.shared["story_notice"] = "Kenji cayo. Reintenta la mision."
            self.game.go("story_mission_select")
            return
        next_fight = int(self.game.shared.get("story_fight_index", 0)) + 1
        if next_fight < len(mission["fights"]):
            self.game.shared["story_fight_index"] = next_fight
            self.game.go("story_battle")
            return
        self.game.progress.complete_mission(mission["number"], mission.get("reward_coins", 0))
        if self.game.auth.logged_in:
            try:
                self.game.auth.sync_progress(self.game.progress.data, self.game.shared.get("online_fighter"))
            except Exception:
                pass
        self.game.shared["story_cutscene_id"] = mission["outro_cutscene"]
        self.game.shared["story_fight_index"] = 0
        if mission["number"] == 1:
            self.game.shared["memory_fragment_id"] = mission.get("memory_fragment")
            self.game.shared["memory_next_scene"] = "story_cutscene"
            self.game.go("memory_fragment")
            return
        self.game.go("story_cutscene")

    def _update_ftue(self):
        if not self._mission().get("ftue") or self.ftue_step >= len(self.FTUE_STEPS) - 1:
            self.story_ai.active = True
            return
        step = self.FTUE_STEPS[self.ftue_step]
        action = step["action"]
        elapsed = self.game.shared.get("story_episode_elapsed", 0.0)
        advance = False
        if action == "move":
            advance = self.game.input.is_down("left") or self.game.input.is_down("right")
        elif action == "approach":
            advance = abs(self.enemy.rect.centerx - self.player.rect.centerx) < 230
        elif action == "light":
            advance = self.game.input.was_pressed("light") or "light" in self.ftue_actions_seen
        elif action == "heavy":
            advance = self.game.input.was_pressed("heavy") or "heavy" in self.ftue_actions_seen
        elif action == "block":
            advance = self.game.input.is_down("block") or "block" in self.ftue_actions_seen
        elif action == "dodge":
            advance = self.game.input.was_pressed("dodge") or "dodge" in self.ftue_actions_seen
        elif action in {"narrative", "stamina"}:
            advance = self.ftue_step_elapsed >= 2.5
        advance = advance or elapsed >= float(step["deadline"])
        if advance:
            self.ftue_step += 1
            self.ftue_step_elapsed = 0.0
            self.ftue_actions_seen.clear()
            if self.ftue_step >= len(self.FTUE_STEPS) - 1:
                self.story_ai.active = True
                self.enemy.health = min(self.enemy.health, 46)

    def update(self, dt):
        mission = self._mission()
        if mission.get("ftue"):
            elapsed = self.game.shared.get("story_episode_elapsed", 0.0) + dt
            self.game.shared["story_episode_elapsed"] = elapsed
            self.ftue_step_elapsed += dt
            if elapsed >= float(mission.get("combat_deadline_seconds", 108)) and self.enemy.health > 0:
                self.ftue_step = len(self.FTUE_STEPS) - 1
                self.story_ai.active = True
                self.enemy.health = 0
                self.enemy.state = "defeated"
                self.combat.round_finished = True
                self.combat.winner = self.player
        if not self._intro_active() and not self._round_transition_active():
            self._update_ftue()
        tutorial_active = mission.get("ftue") and self.ftue_step < len(self.FTUE_STEPS) - 1
        protected_enemy_health = self.enemy.health if tutorial_active else None
        if tutorial_active and not self._intro_active() and not self._round_transition_active():
            self.enemy.health = 1000
        super().update(dt)
        if protected_enemy_health is not None and self.enemy.health > 0:
            self.enemy.health = protected_enemy_health

    def draw(self, surface):
        super().draw(surface)
        mission = self._mission()
        fight_number = int(self.game.shared.get("story_fight_index", 0)) + 1
        draw_chip(surface, pygame.Rect(500, 108, 280, 30), f"{mission['title'].upper()} - {fight_number}/{len(mission['fights'])}", accent=RED)
        if mission.get("ftue") and not self._intro_active() and self.ftue_step < len(self.FTUE_STEPS):
            step = self.FTUE_STEPS[self.ftue_step]
            draw_panel(surface, pygame.Rect(326, 148, 628, 104), title=step["title"])
            text = get_font("body", 21, bold=True).render(step["detail"], True, LIGHT)
            surface.blit(text, text.get_rect(center=(640, 212)))
            stamina = get_font("tiny", 17, bold=True).render(
                f"STAMINA {int(self.player.stamina)}/{int(self.player.stats.max_stamina)} - se regenera automaticamente.",
                True,
                GREEN,
            )
            surface.blit(stamina, stamina.get_rect(center=(640, 238)))
        if mission.get("ftue"):
            limit = int(mission.get("max_duration_seconds", 120))
            remaining = max(0, limit - int(self.game.shared.get("story_episode_elapsed", 0.0)))
            timer = get_font("tiny", 17, bold=True).render(f"MISION 1  {remaining // 60}:{remaining % 60:02d}", True, GOLD)
            surface.blit(timer, timer.get_rect(topright=(1230, 112)))
