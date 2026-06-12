from pathlib import Path
import json

import pygame

from src.core.audio_manager import AudioManager
from src.core.constants import FPS, HEIGHT, WIDTH, SCENE_SPLASH
from src.core.input_manager import InputManager
from src.core.platform_detection import detect_runtime_platform, platform_display_name, platform_runtime_message
from src.core.scene_manager import SceneManager
from src.network.network_client import NetworkClient
from src.scenes.arena_select import ArenaSelectScene
from src.scenes.battle_scene import BattleScene
from src.scenes.character_select import CharacterSelectScene
from src.scenes.lobby_scene import LobbyScene
from src.scenes.main_menu import MainMenuScene
from src.scenes.online_battle_scene import OnlineBattleScene
from src.scenes.online_menu import OnlineMenuScene
from src.scenes.pause_menu import PauseMenuScene
from src.scenes.platform_select import PlatformSelectScene
from src.scenes.result_scene import ResultScene
from src.scenes.splash_screen import SplashScreenScene
from src.utils.asset_loader import AssetLoader
from src.utils.json_loader import load_json


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Samurai Arena Fight")
        self.root = Path(__file__).resolve().parents[2]
        self.client_dir = self.root
        self.settings_path = self.client_dir / "config" / "settings.json"
        self.settings = load_json(self.settings_path, {})
        self.settings.setdefault("screen_width", WIDTH)
        self.settings.setdefault("screen_height", HEIGHT)
        self.settings.setdefault("fps", FPS)
        self.settings.setdefault("fullscreen", False)
        self.settings.setdefault("platform", "pc")
        self.settings.setdefault("master_volume", 1.0)
        self.settings.setdefault("music_volume", 0.7)
        self.settings.setdefault("sfx_volume", 0.8)
        self.settings.setdefault("music_enabled", True)
        self.settings.setdefault("server_url", "http://localhost:3000")
        self.settings.setdefault("username", "player")
        self.detected_platform = detect_runtime_platform()
        self.detected_platform_label = platform_display_name(self.detected_platform)
        self.detected_platform_message = platform_runtime_message(self.detected_platform)
        self.settings["platform"] = self.detected_platform
        self.assets = AssetLoader(self.client_dir)
        self.audio = AudioManager(self.client_dir, self.settings)
        self.audio.load_sound("hit_light", "assets/audio/hit_light.wav")
        self.audio.load_sound("hit_heavy", "assets/audio/hit_heavy.wav")
        self.audio.load_sound("hit_kick", "assets/audio/hit_kick.wav")
        self.audio.load_sound("count_tick", "assets/audio/count_tick.wav")
        self.audio.load_sound("fight_start", "assets/audio/fight_start.wav")
        self.network = NetworkClient(self.settings["server_url"])
        self.input = InputManager(self.detected_platform)
        flags = pygame.FULLSCREEN if self.settings["fullscreen"] else 0
        self.screen = pygame.display.set_mode(
            (self.settings["screen_width"], self.settings["screen_height"]), flags
        )
        self.clock = pygame.time.Clock()
        self.scene_manager = SceneManager(self)
        self.shared = {
            "selected_platform": self.detected_platform,
            "selected_platform_label": self.detected_platform_label,
            "platform_detection_mode": "auto",
            "selected_fighter": "kenji",
            "selected_arena": "coliseo_de_acero",
            "match_mode": "local",
            "online_room": None,
            "online_role": None,
            "online_username": self.settings.get("username", "player"),
            "online_ready": False,
            "online_match_data": None,
            "result": None,
        }
        self.running = True
        self.scenes = {}
        self._build_scenes()
        self.scene_manager.change(self.scenes[SCENE_SPLASH])

    def _build_scenes(self):
        self.scenes = {
            "splash": SplashScreenScene(self),
            "platform": PlatformSelectScene(self),
            "menu": MainMenuScene(self),
            "online_menu": OnlineMenuScene(self),
            "lobby": LobbyScene(self),
            "character": CharacterSelectScene(self),
            "arena": ArenaSelectScene(self),
            "battle": BattleScene(self),
            "online_battle": OnlineBattleScene(self),
            "pause": PauseMenuScene(self),
            "result": ResultScene(self),
        }

    def save_settings(self):
        self.settings["platform"] = self.detected_platform
        self.settings["music_enabled"] = self.audio.music_enabled
        self.settings["server_url"] = self.network.server_url
        self.settings["username"] = self.shared.get("online_username", self.settings.get("username", "player"))
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")

    def toggle_music(self):
        self.audio.toggle_music()
        self.save_settings()
        self._update_audio_for_scene(self.scene_manager.current_scene)

    def _update_audio_for_scene(self, scene):
        menu_scene_names = {
            "menu",
            "platform",
            "character",
            "arena",
            "online_menu",
            "lobby",
            "result",
        }
        for key, candidate in self.scenes.items():
            if candidate is scene:
                if key in menu_scene_names:
                    self.audio.play_menu_music()
                else:
                    self.audio.stop_music()
                return

    def go(self, key):
        self.scene_manager.change(self.scenes[key])
        self._update_audio_for_scene(self.scenes[key])

    def run(self):
        while self.running:
            dt = self.clock.tick(self.settings["fps"]) / 1000.0
            self.input.begin_frame()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.input.handle_event(event)
                self.scene_manager.handle_event(event)
            self.scene_manager.update(dt)
            self.screen.fill((12, 10, 12))
            self.scene_manager.draw(self.screen)
            pygame.display.flip()
        pygame.quit()
