from pathlib import Path

import pygame


class AudioManager:
    def __init__(self, root, settings):
        self.root = Path(root)
        self.settings = settings
        self.available = False
        self.music_enabled = settings.get("music_enabled", True)
        self.sounds = {}
        self.current_music = None
        self._init_mixer()
        self._configure_volumes()

    def _init_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.available = True
        except pygame.error:
            self.available = False

    def _configure_volumes(self):
        self.master_volume = float(self.settings.get("master_volume", 1.0))
        self.music_volume = float(self.settings.get("music_volume", 0.7))
        self.sfx_volume = float(self.settings.get("sfx_volume", 0.8))
        if self.available:
            pygame.mixer.music.set_volume(self._music_volume())

    def _music_volume(self):
        if not self.music_enabled:
            return 0.0
        return max(0.0, min(1.0, self.master_volume * self.music_volume))

    def _sfx_volume(self):
        return max(0.0, min(1.0, self.master_volume * self.sfx_volume))

    def load_sound(self, key, relative_path):
        if not self.available:
            return
        if key in self.sounds:
            return
        path = self.root / relative_path
        if not path.exists():
            return
        sound = pygame.mixer.Sound(str(path))
        sound.set_volume(self._sfx_volume())
        self.sounds[key] = sound

    def refresh_settings(self, settings):
        self.settings = settings
        self.music_enabled = settings.get("music_enabled", self.music_enabled)
        self._configure_volumes()
        for sound in self.sounds.values():
            sound.set_volume(self._sfx_volume())

    def play_sound(self, key):
        if not self.available or key not in self.sounds:
            return
        self.sounds[key].play()

    def play_hit(self, attack_type):
        key_map = {
            "attack_light": "hit_light",
            "attack_heavy": "hit_heavy",
            "kick": "hit_kick",
            "low_kick": "hit_kick",
            "flying_kick": "hit_kick",
        }
        self.play_sound(key_map.get(attack_type, "hit_light"))

    def play_count_tick(self):
        self.play_sound("count_tick")

    def play_fight(self):
        self.play_sound("fight_start")

    def play_menu_music(self):
        if not self.available:
            return
        if not self.music_enabled:
            self.stop_music()
            return
        music_path = self.root / "assets" / "audio" / "menu_theme.wav"
        if not music_path.exists():
            return
        if self.current_music != "menu_theme":
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.play(-1, fade_ms=280)
            self.current_music = "menu_theme"
        pygame.mixer.music.set_volume(self._music_volume())
        if self.music_enabled and not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1, fade_ms=180)

    def stop_music(self):
        if not self.available:
            return
        pygame.mixer.music.fadeout(220)
        self.current_music = None

    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if not self.available:
            return self.music_enabled
        if self.music_enabled:
            pygame.mixer.music.set_volume(self._music_volume())
            if self.current_music == "menu_theme" and not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1, fade_ms=180)
        else:
            pygame.mixer.music.set_volume(0.0)
            pygame.mixer.music.fadeout(180)
            self.current_music = None
        return self.music_enabled
