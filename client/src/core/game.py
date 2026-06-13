from pathlib import Path
import json
import os

import pygame

from src.core.audio_manager import AudioManager
from src.core.constants import FPS, HEIGHT, WIDTH, SCENE_SPLASH
from src.core.input_manager import InputManager
from src.core.platform_detection import detect_runtime_platform, platform_display_name, platform_runtime_message
from src.core.scene_manager import SceneManager
from src.network.network_client import NetworkClient
from src.network.auth_client import AuthClient
from src.scenes.account_scene import AccountScene
from src.scenes.arena_select import ArenaSelectScene
from src.scenes.battle_scene import BattleScene
from src.scenes.character_select import CharacterSelectScene
from src.scenes.lobby_scene import LobbyScene
from src.scenes.main_menu import MainMenuScene
from src.scenes.login_scene import LoginScene
from src.scenes.memory_fragment_scene import MemoryFragmentScene
from src.scenes.online_character_create import OnlineCharacterCreateScene
from src.scenes.online_battle_scene import OnlineBattleScene
from src.scenes.online_menu import OnlineMenuScene
from src.scenes.pause_menu import PauseMenuScene
from src.scenes.platform_select import PlatformSelectScene
from src.scenes.result_scene import ResultScene
from src.scenes.register_scene import RegisterScene
from src.scenes.splash_screen import SplashScreenScene
from src.scenes.story_battle_scene import StoryBattleScene
from src.scenes.story_cutscene_scene import StoryCutsceneScene
from src.scenes.story_dialogue_scene import StoryDialogueScene
from src.scenes.story_intro import StoryIntroScene
from src.scenes.story_map import StoryMapScene
from src.scenes.story_mission_select import StoryMissionSelectScene
from src.utils.asset_loader import AssetLoader
from src.utils.json_loader import load_json
from src.utils.progress_manager import ProgressManager
from src.utils.session_storage import SessionStorage


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
        self.settings.setdefault("server_url", "https://samurai-arena-fight.onrender.com")
        self.settings["server_url"] = os.environ.get("SAMURAI_SERVER_URL", self.settings["server_url"])
        self.settings.setdefault("username", "player")
        self.detected_platform = detect_runtime_platform()
        self.detected_platform_label = platform_display_name(self.detected_platform)
        self.detected_platform_message = platform_runtime_message(self.detected_platform)
        self.settings["platform"] = self.detected_platform
        self.assets = AssetLoader(self.client_dir)
        self.progress = ProgressManager(self.client_dir)
        self.session_storage = SessionStorage(self.client_dir)
        self.auth = AuthClient(self.settings["server_url"], self.session_storage)
        self.audio = AudioManager(self.client_dir, self.settings)
        self.audio.load_sound("hit_light", "assets/audio/hit_light.wav")
        self.audio.load_sound("hit_heavy", "assets/audio/hit_heavy.wav")
        self.audio.load_sound("hit_kick", "assets/audio/hit_kick.wav")
        self.audio.load_sound("count_tick", "assets/audio/count_tick.wav")
        self.audio.load_sound("fight_start", "assets/audio/fight_start.wav")
        self.network = NetworkClient(self.settings["server_url"], auth_token=self.auth.token)
        self.input = InputManager(self.detected_platform)
        self.logical_size = (self.settings["screen_width"], self.settings["screen_height"])
        if self.detected_platform == "android":
            self.display_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.screen = pygame.Surface(self.logical_size).convert()
            self.target_fps = min(45, int(self.settings["fps"]))
        else:
            flags = pygame.FULLSCREEN if self.settings["fullscreen"] else 0
            self.display_surface = pygame.display.set_mode(self.logical_size, flags)
            self.screen = self.display_surface
            self.target_fps = int(self.settings["fps"])
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
            "result_detail": None,
            "account_user": None,
            "auth_return_scene": None,
            "online_fighter": None,
            "story_mission": max(1, int(self.progress.data.get("story_mission", 0)) + 1),
            "story_fight_index": 0,
            "story_cutscene_id": "prologue",
            "memory_fragment_id": None,
            "story_episode_elapsed": 0.0,
            "story_episode_active": False,
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
            "login": LoginScene(self),
            "register": RegisterScene(self),
            "account": AccountScene(self),
            "online_character_create": OnlineCharacterCreateScene(self),
            "online_menu": OnlineMenuScene(self),
            "lobby": LobbyScene(self),
            "character": CharacterSelectScene(self),
            "arena": ArenaSelectScene(self),
            "battle": BattleScene(self),
            "online_battle": OnlineBattleScene(self),
            "pause": PauseMenuScene(self),
            "result": ResultScene(self),
            "story_intro": StoryIntroScene(self),
            "story_map": StoryMapScene(self),
            "story_mission_select": StoryMissionSelectScene(self),
            "story_battle": StoryBattleScene(self),
            "story_dialogue": StoryDialogueScene(self),
            "story_cutscene": StoryCutsceneScene(self),
            "memory_fragment": MemoryFragmentScene(self),
        }

    def save_settings(self):
        self.settings["platform"] = self.detected_platform
        self.settings["music_enabled"] = self.audio.music_enabled
        if not os.environ.get("SAMURAI_SERVER_URL"):
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
            "login",
            "register",
            "account",
            "online_character_create",
            "story_map",
            "story_mission_select",
            "story_dialogue",
            "memory_fragment",
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

    def _logical_position(self, display_position):
        display_width, display_height = self.display_surface.get_size()
        logical_width, logical_height = self.logical_size
        scale = min(display_width / logical_width, display_height / logical_height)
        viewport_width = logical_width * scale
        viewport_height = logical_height * scale
        offset_x = (display_width - viewport_width) / 2
        offset_y = (display_height - viewport_height) / 2
        x = int((display_position[0] - offset_x) / scale)
        y = int((display_position[1] - offset_y) / scale)
        return max(0, min(logical_width - 1, x)), max(0, min(logical_height - 1, y))

    def _normalize_event(self, event):
        if self.screen is self.display_surface:
            return event
        if event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION}:
            attributes = dict(event.dict)
            attributes["pos"] = self._logical_position(event.pos)
            return pygame.event.Event(event.type, attributes)
        if event.type in {pygame.FINGERDOWN, pygame.FINGERUP, pygame.FINGERMOTION}:
            display_size = self.display_surface.get_size()
            pos = self._logical_position((event.x * display_size[0], event.y * display_size[1]))
            event_type = pygame.MOUSEBUTTONDOWN if event.type == pygame.FINGERDOWN else pygame.MOUSEBUTTONUP if event.type == pygame.FINGERUP else pygame.MOUSEMOTION
            return pygame.event.Event(event_type, {"pos": pos, "button": 1, "rel": (0, 0), "buttons": (1, 0, 0)})
        return event

    def _present(self):
        if self.screen is self.display_surface:
            pygame.display.flip()
            return
        display_width, display_height = self.display_surface.get_size()
        logical_width, logical_height = self.logical_size
        scale = min(display_width / logical_width, display_height / logical_height)
        target_size = (max(1, int(logical_width * scale)), max(1, int(logical_height * scale)))
        frame = pygame.transform.smoothscale(self.screen, target_size)
        self.display_surface.fill((0, 0, 0))
        self.display_surface.blit(frame, frame.get_rect(center=(display_width // 2, display_height // 2)))
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(self.target_fps) / 1000.0
            self.input.begin_frame()
            for raw_event in pygame.event.get():
                event = self._normalize_event(raw_event)
                if event.type == pygame.QUIT:
                    self.running = False
                self.input.handle_event(event)
                self.scene_manager.handle_event(event)
            self.scene_manager.update(dt)
            self.screen.fill((12, 10, 12))
            self.scene_manager.draw(self.screen)
            self._present()
        pygame.quit()
