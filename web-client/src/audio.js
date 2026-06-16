function createLoopingAudio(src) {
  const audio = new Audio(src);
  audio.loop = true;
  audio.preload = "auto";
  return audio;
}

export class WebAudioManager {
  constructor(settings, assetUrl) {
    this.settings = settings;
    this.assetUrl = assetUrl;
    this.scene = "splash";
    this.unlocked = false;
    this.audioContext = null;
    this.menuMusic = createLoopingAudio(this.assetUrl("assets/audio/menu_theme.wav"));
    this.effects = {
      countTick: this.assetUrl("assets/audio/count_tick.wav"),
      fightStart: this.assetUrl("assets/audio/fight_start.wav"),
      hitLight: this.assetUrl("assets/audio/hit_light.wav"),
      hitHeavy: this.assetUrl("assets/audio/hit_heavy.wav"),
      hitKick: this.assetUrl("assets/audio/hit_kick.wav"),
    };
    this.handleUnlock = this.handleUnlock.bind(this);
    document.addEventListener("pointerdown", this.handleUnlock, { passive: true });
    document.addEventListener("keydown", this.handleUnlock);
  }

  destroy() {
    document.removeEventListener("pointerdown", this.handleUnlock);
    document.removeEventListener("keydown", this.handleUnlock);
    this.stopMenuMusic();
  }

  handleUnlock() {
    if (this.unlocked) return;
    this.unlocked = true;
    this.ensureAudioContext();
    this.audioContext?.resume?.().catch(() => {});
    this.applyScene();
  }

  setSettings(settings) {
    this.settings = settings;
    this.applyScene();
  }

  setScene(scene) {
    this.scene = scene;
    this.applyScene();
  }

  isMusicEnabled() {
    return !this.settings.musicMuted;
  }

  isFxEnabled() {
    return !this.settings.fxMuted;
  }

  shouldPlayMenuMusic() {
    return ["menu", "quick", "story", "online", "options", "cutscene"].includes(this.scene);
  }

  applyScene() {
    if (!this.unlocked) return;
    if (this.isMusicEnabled() && this.shouldPlayMenuMusic()) {
      this.playMenuMusic();
      return;
    }
    this.stopMenuMusic();
  }

  playMenuMusic() {
    this.menuMusic.volume = 0.52;
    this.menuMusic.play().catch(() => {});
  }

  stopMenuMusic() {
    this.menuMusic.pause();
    this.menuMusic.currentTime = 0;
  }

  toggleMusic() {
    this.settings.musicMuted = !this.settings.musicMuted;
    this.applyScene();
    return {
      musicMuted: this.settings.musicMuted,
    };
  }

  toggleFx() {
    this.settings.fxMuted = !this.settings.fxMuted;
    return {
      fxMuted: this.settings.fxMuted,
    };
  }

  ensureAudioContext() {
    if (this.audioContext) return this.audioContext;
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return null;
    this.audioContext = new AudioContextClass();
    return this.audioContext;
  }

  playUiTapTone() {
    const context = this.ensureAudioContext();
    if (!context) return;
    const now = context.currentTime;
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.type = "triangle";
    oscillator.frequency.setValueAtTime(680, now);
    oscillator.frequency.exponentialRampToValueAtTime(420, now + 0.07);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.04, now + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.09);
    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.start(now);
    oscillator.stop(now + 0.1);
  }

  playEffect(key) {
    if (!this.unlocked || !this.isFxEnabled()) return;
    if (key === "uiTap") {
      this.playUiTapTone();
      return;
    }
    const src = this.effects[key];
    if (!src) return;
    const audio = new Audio(src);
    audio.volume = key === "fightStart" ? 0.9 : 0.74;
    audio.play().catch(() => {});
  }
}
