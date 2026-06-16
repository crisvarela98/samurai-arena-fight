import { resolveRuntimeConfig } from "./config.js";
import { WebAudioManager } from "./audio.js";
import { ApiClient, RealtimeClient } from "./net.js";
import {
  buildCompletedMissionProgress,
  clearAuth,
  loadAuth,
  loadOnlineProfile,
  loadProgress,
  loadSettings,
  saveAuth,
  saveOnlineProfile,
  saveProgress,
  saveSettings,
} from "./storage.js";
import { BattleView } from "./battle.js";

function unique(list) {
  return [...new Set(list)];
}

function button(label, action, variant = "") {
  return `<button type="button" class="menu-btn ${variant}" data-action="${action}">${label}</button>`;
}

function rankingFilterButton(label, value, activeValue) {
  return `<button type="button" class="rank-filter ${value === activeValue ? "active" : ""}" data-action="set-ranking-range" data-value="${value}">${label}</button>`;
}

function rankingViewButton(label, value, activeValue) {
  return `<button type="button" class="rank-view-tab ${value === activeValue ? "active" : ""}" data-action="set-ranking-view" data-value="${value}">${label}</button>`;
}

function backendLabel(url) {
  if (!url) return "BACKEND AUTO";
  try {
    const parsed = new URL(url);
    return parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1" ? "BACKEND LOCAL" : `API ${parsed.hostname}`;
  } catch (_error) {
    return `API ${url}`;
  }
}

function cloneSceneParams(params = {}) {
  try {
    return structuredClone(params);
  } catch (_error) {
    return JSON.parse(JSON.stringify(params || {}));
  }
}

function sameSceneState(left, right) {
  return left?.scene === right?.scene && JSON.stringify(left?.params || {}) === JSON.stringify(right?.params || {});
}

export class SamuraiArenaWebApp {
  constructor(root, data) {
    this.root = root;
    this.data = data;
    this.settings = loadSettings();
    this.progress = loadProgress();
    this.auth = loadAuth();
    this.rememberAuth = Boolean(this.auth.token);
    this.onlineProfile = loadOnlineProfile();
    this.runtimeConfig = resolveRuntimeConfig(this.settings);
    this.api = new ApiClient(() => this.runtimeConfig, () => this.auth.token);
    this.realtime = new RealtimeClient(() => this.runtimeConfig, () => this.auth.token);
    this.audio = new WebAudioManager(this.settings, data.assetUrl);
    this.scene = "splash";
    this.sceneParams = {};
    this.battle = null;
    this.roomSnapshot = null;
    this.onlineLists = { rooms: [], ranking: [], clanRanking: [], rankingSummary: null };
    this.renderVersion = 0;
    this.sceneHistory = [];
    this.historyReady = false;
    this.handleBrowserBack = this.handleBrowserBack.bind(this);
    this.bindRealtime();
  }

  bindRealtime() {
    this.realtime.on("room_created", (payload) => {
      this.roomSnapshot = payload;
      this.renderLobby(payload, "Esperando rival...");
    });
    this.realtime.on("waiting_for_player", (payload) => {
      this.roomSnapshot = payload;
      this.renderLobby(payload, "Comparti el codigo y espera.");
    });
    this.realtime.on("room_joined", (payload) => {
      this.roomSnapshot = payload;
      this.renderLobby(payload, "Sala lista. Esperando inicio.");
    });
    this.realtime.on("match_started", (payload) => {
      this.roomSnapshot = payload;
      this.startOnlineBattle(payload);
    });
    this.realtime.on("error_message", (payload) => {
      this.toast(payload.message || "Error online");
    });
  }

  async init() {
    this.setupBackNavigation();
    this.renderFrame();
    this.audio.setScene("splash");
    if (this.auth.token) {
      try {
        const payload = await this.api.me();
        this.auth.user = payload.user;
        saveAuth(this.auth);
      } catch (_error) {
        clearAuth();
        this.auth = loadAuth();
        this.rememberAuth = false;
      }
    }
    setTimeout(() => this.go("menu", {}, { resetHistoryRoot: true }), 2000);
  }

  themeUrl(fileName) {
    return this.data.assetUrl(`assets/ui/${fileName}`);
  }

  renderAudioToggle(action, label, enabled, size = "") {
    return `<button type="button" class="sound-toggle ${size}" data-action="${action}"><span class="sound-indicator ${enabled ? "on" : "off"}"></span>${label} ${enabled ? "ON" : "OFF"}</button>`;
  }

  rankingRangeMeta(range) {
    if (range === "today") {
      return {
        title: "Hoy",
        subtitle: "Resultados del dia segun la zona horaria del dispositivo.",
      };
    }
    if (range === "week") {
      return {
        title: "Semana",
        subtitle: "Ultimos 7 dias de actividad online.",
      };
    }
    return {
      title: "Global",
      subtitle: "Tabla historica acumulada de todo el juego.",
    };
  }

  storyActLabel() {
    const act = Math.max(1, Number(this.progress.story_act || 1));
    const actTitles = {
      1: "EL DESPERTAR",
    };
    return actTitles[act] ? `ACTO ${act} - ${actTitles[act]}` : `ACTO ${act}`;
  }

  previewHonorPoints() {
    return 0;
  }

  authSceneState(params = this.sceneParams) {
    return {
      authMode: params.authMode === "register" ? "register" : "login",
      rememberAuth: params.rememberAuth !== false,
    };
  }

  applyAuthenticatedUser(result, rememberAuth = true) {
    this.auth = result;
    this.rememberAuth = rememberAuth;
    if (rememberAuth) {
      saveAuth(this.auth);
    } else {
      clearAuth();
    }
    this.onlineProfile.username = result.user.username;
    saveOnlineProfile(this.onlineProfile);
  }

  async submitAuthLogin(form, rememberAuth = true) {
    const payload = new FormData(form);
    const identity = String(payload.get("identity") || "").trim();
    const password = String(payload.get("password") || "");
    if (!identity || !password) {
      this.toast("Completa usuario o mail y la contrasena.");
      return false;
    }
    try {
      const result = await this.api.login(identity, password);
      this.applyAuthenticatedUser(result, rememberAuth);
      return true;
    } catch (error) {
      this.toast(error.message);
      return false;
    }
  }

  async submitAuthRegister(form, rememberAuth = true) {
    const payload = new FormData(form);
    const username = String(payload.get("username") || "").trim();
    const email = String(payload.get("email") || "").trim().toLowerCase();
    const password = String(payload.get("password") || "");
    if (username.length < 3) {
      this.toast("El usuario debe tener al menos 3 caracteres.");
      return false;
    }
    if (!email.includes("@")) {
      this.toast("Ingresa un mail valido.");
      return false;
    }
    if (!/^\d{8}$/.test(password)) {
      this.toast("La contrasena debe tener 8 digitos.");
      return false;
    }
    try {
      const result = await this.api.register(username, email, password);
      this.applyAuthenticatedUser(result, rememberAuth);
      return true;
    } catch (error) {
      this.toast(error.message);
      return false;
    }
  }

  syncSettings() {
    saveSettings(this.settings);
    this.runtimeConfig = resolveRuntimeConfig(this.settings);
    this.audio.setSettings(this.settings);
  }

  toggleMusic() {
    const next = this.audio.toggleMusic();
    this.settings.musicMuted = next.musicMuted;
    this.syncSettings();
    this.renderFrame();
  }

  toggleFx() {
    const next = this.audio.toggleFx();
    this.settings.fxMuted = next.fxMuted;
    this.syncSettings();
    if (!this.settings.fxMuted) {
      this.audio.playEffect("uiTap");
    }
    this.renderFrame();
  }

  setupBackNavigation() {
    if (this.historyReady || typeof window === "undefined") return;
    this.historyReady = true;
    this.sceneHistory = [{ scene: this.scene, params: cloneSceneParams(this.sceneParams) }];
    window.addEventListener("popstate", this.handleBrowserBack);
    window.history.replaceState({ __samuraiArenaFight: true, guard: true }, "");
    window.history.pushState({ __samuraiArenaFight: true, cursor: 0 }, "");
  }

  resetBackNavigationRoot(scene = this.scene, params = this.sceneParams) {
    if (!this.historyReady || typeof window === "undefined") return;
    this.sceneHistory = [{ scene, params: cloneSceneParams(params) }];
    window.history.replaceState({ __samuraiArenaFight: true, guard: true }, "");
    window.history.pushState({ __samuraiArenaFight: true, cursor: 0 }, "");
  }

  pushBackNavigation(scene = this.scene, params = this.sceneParams) {
    if (!this.historyReady || typeof window === "undefined") return;
    const snapshot = { scene, params: cloneSceneParams(params) };
    const previous = this.sceneHistory[this.sceneHistory.length - 1];
    if (sameSceneState(previous, snapshot)) return;
    this.sceneHistory.push(snapshot);
    window.history.pushState({ __samuraiArenaFight: true, cursor: this.sceneHistory.length - 1 }, "");
  }

  handleBrowserBack(event) {
    const state = event.state;
    if (!state?.__samuraiArenaFight) {
      window.history.pushState({ __samuraiArenaFight: true, cursor: Math.max(0, this.sceneHistory.length - 1) }, "");
      return;
    }
    if (state.guard) {
      window.history.pushState({ __samuraiArenaFight: true, cursor: Math.max(0, this.sceneHistory.length - 1) }, "");
      return;
    }
    const cursor = Math.max(0, Math.min(Number(state.cursor || 0), this.sceneHistory.length - 1));
    const target = this.sceneHistory[cursor];
    if (!target) {
      window.history.pushState({ __samuraiArenaFight: true, cursor: Math.max(0, this.sceneHistory.length - 1) }, "");
      return;
    }
    this.sceneHistory = this.sceneHistory.slice(0, cursor + 1);
    this.go(target.scene, target.params, { fromHistory: true });
  }

  go(scene, params = {}, options = {}) {
    if (this.battle) {
      this.battle.destroy();
      this.battle = null;
    }
    this.scene = scene;
    this.sceneParams = params;
    this.audio.setScene(scene);
    this.renderFrame();
    if (options.resetHistoryRoot) {
      this.resetBackNavigationRoot(scene, params);
      return;
    }
    if (!options.fromHistory) {
      this.pushBackNavigation(scene, params);
    }
  }

  renderFrame() {
    this.renderVersion += 1;
    this.root.innerHTML = `<div class="shell"><div class="app-stage"></div></div>`;
    this.stage = this.root.querySelector(".app-stage");
    if (this.scene === "splash") {
      this.renderSplash();
      return;
    }
    if (this.scene === "battle") {
      this.mountBattle();
      return;
    }
    this.renderScene();
  }

  renderSplash() {
    this.stage.innerHTML = `
      <section class="splash-screen splash-dark">
        <div class="splash-card">
          <div class="logo-slot">TU LOGO / STUDIO</div>
          <div class="logo-slot game">SAMURAI ARENA FIGHT</div>
        </div>
      </section>
    `;
  }

  renderScene() {
    switch (this.scene) {
      case "menu":
        this.renderMenu();
        break;
      case "quick":
        this.renderQuickSetup();
        break;
      case "story":
        this.renderStoryMenu();
        break;
      case "online":
        this.renderOnlineMenu();
        break;
      case "options":
        this.renderOptions();
        break;
      default:
        this.go("menu");
    }
  }

  renderMenu() {
    const canOnline = this.progress.first_time_completed || this.progress.unlocked_modes.includes("Online");
    const showGuestAccess = !this.auth.token;
    const honorPoints = Number(this.auth.user?.honorPoints ?? this.previewHonorPoints());
    const currentLevel = Number(this.auth.user?.level || Math.max(1, Math.floor(honorPoints / 250) + 1));
    this.stage.innerHTML = `
      <section class="scene menu-scene clean-menu scene-backdrop" style="--scene-image: url('${this.themeUrl("menu_main_bg_v2.png")}')">
        <div class="scene-overlay scene-overlay-menu"></div>
        <div class="scene-topbar menu-topbar">
          <div class="story-act-box">
            <span class="eyebrow">Modo historia</span>
            <strong class="story-act-value">${this.storyActLabel()}</strong>
          </div>
        </div>

        <div class="vintage-menu-panel menu-panel-main">
          <span class="eyebrow">Principal</span>
          <h2>Elegi tu camino</h2>
          <div class="menu-actions vertical">
            ${button("Juego rapido", "quick")}
            ${button("Modo historia", "story")}
            ${button("Online", "online", canOnline ? "" : "disabled")}
            ${button("Opciones", "options")}
          </div>
          <div class="status-row">
            <span class="pill">${backendLabel(this.runtimeConfig.apiBaseUrl)}</span>
            <span class="pill">${this.auth.user ? `SESION ${this.auth.user.username}` : "INVITADO"}</span>
          </div>
        </div>
        <div class="menu-auth-footer">
          <div class="menu-footer-profile">
            <div class="menu-auth-copy">
              <span class="eyebrow">${this.auth.user ? "Perfil online" : "Invitado"}</span>
              <strong>${this.auth.user ? this.auth.user.username : "Los puntos de honor se ganan solo online"}</strong>
            </div>
            <div class="pill-row menu-footer-pills">
              <span class="pill accent">HONOR ${honorPoints}</span>
              <span class="pill">LVL ${currentLevel}</span>
              <span class="pill">${this.auth.user ? "Solo online" : "Sin sesion"}</span>
            </div>
          </div>
          ${
            showGuestAccess
              ? `
                <div class="menu-auth-actions">
                  ${button("Iniciar sesion", "open-login", "ghost")}
                  ${button("Registrarse", "open-register")}
                </div>
              `
              : `
                <div class="menu-footer-session">
                  <span class="pill">${this.auth.user?.email || "Cuenta activa"}</span>
                  <span class="pill">${this.auth.user?.wins || 0}V / ${this.auth.user?.losses || 0}D</span>
                </div>
              `
          }
        </div>
      </section>
    `;
    this.bindActions({
      quick: () => this.go("quick"),
      story: () => this.go("story"),
      online: () => {
        if (!canOnline) {
          this.toast("Termina la mision 1 para desbloquear Online.");
          return;
        }
        this.go("online", { onlineStep: "clan-entry" });
      },
      options: () => this.go("options"),
      "open-login": () => this.go("online", { authMode: "login", rememberAuth: true, onlineStep: "clan-entry" }),
      "open-register": () => this.go("online", { authMode: "register", rememberAuth: true, onlineStep: "clan-entry" }),
    });
  }

  renderQuickSetup() {
    const fighters = this.data.fighters;
    const arenas = this.data.arenas;
    const selectedFighter = this.sceneParams.fighterId || fighters[0].id;
    const selectedEnemy = this.sceneParams.enemyId || fighters[1].id;
    const selectedArena = this.sceneParams.arenaId || arenas[0].id;
    this.stage.innerHTML = `
      <section class="scene card-scene scene-backdrop" style="--scene-image: url('${this.themeUrl("menu_armory_bg.png")}')">
        <div class="scene-overlay"></div>
        <div class="scene-header">
          <h2>Juego rapido</h2>
          <div class="inline-actions">
            ${button("Volver", "back", "ghost")}
          </div>
        </div>
        <div class="selection-grid">
          <div class="card">
            <h3>Tu guerrero</h3>
            <div class="selector-list">
              ${fighters
                .map(
                  (fighter) => `
                    <button type="button" class="select-card ${fighter.id === selectedFighter ? "active" : ""}" data-action="pick-fighter" data-value="${fighter.id}">
                      <img src="${this.data.assetUrl(fighter.portrait)}" alt="${fighter.name}" />
                      <span>${fighter.name}</span>
                    </button>
                  `,
                )
                .join("")}
            </div>
          </div>
          <div class="card">
            <h3>Rival</h3>
            <div class="selector-list">
              ${fighters
                .map(
                  (fighter) => `
                    <button type="button" class="select-card ${fighter.id === selectedEnemy ? "active" : ""}" data-action="pick-enemy" data-value="${fighter.id}">
                      <img src="${this.data.assetUrl(fighter.portrait)}" alt="${fighter.name}" />
                      <span>${fighter.name}</span>
                    </button>
                  `,
                )
                .join("")}
            </div>
          </div>
          <div class="card">
            <h3>Arena</h3>
            <div class="selector-list arena-list">
              ${arenas
                .map(
                  (arena) => `
                    <button type="button" class="arena-card ${arena.id === selectedArena ? "active" : ""}" data-action="pick-arena" data-value="${arena.id}">
                      <img src="${arena.backgroundUrl}" alt="${arena.name}" />
                      <span>${arena.name}</span>
                    </button>
                  `,
                )
                .join("")}
            </div>
          </div>
        </div>
        <div class="footer-actions">
          ${button("Entrar a la arena", "start-quick")}
        </div>
      </section>
    `;
    this.bindActions({
      back: () => this.go("menu"),
      "pick-fighter": (event) =>
        this.go("quick", { fighterId: event.currentTarget.dataset.value, enemyId: selectedEnemy, arenaId: selectedArena }),
      "pick-enemy": (event) =>
        this.go("quick", { fighterId: selectedFighter, enemyId: event.currentTarget.dataset.value, arenaId: selectedArena }),
      "pick-arena": (event) =>
        this.go("quick", { fighterId: selectedFighter, enemyId: selectedEnemy, arenaId: event.currentTarget.dataset.value }),
      "start-quick": () =>
        this.go("battle", {
          mode: "quick",
          fighterId: selectedFighter,
          enemyId: selectedEnemy,
          arenaId: selectedArena,
        }),
    });
  }

  renderStoryMenu() {
    const unlockedMission = Math.max(1, Number(this.progress.story_mission || 0) + 1);
    this.stage.innerHTML = `
      <section class="scene card-scene scene-backdrop" style="--scene-image: url('${this.themeUrl("menu_armory_bg.png")}')">
        <div class="scene-overlay"></div>
        <div class="scene-header">
          <h2>Modo historia</h2>
          <div class="inline-actions">
            ${button("Volver", "back", "ghost")}
          </div>
        </div>
        <div class="story-banner">
          <div>
            <span class="eyebrow">ACTO 1 - EL DESPERTAR</span>
            <h3>Entre los muertos</h3>
            <p>FTUE narrativo de 2 minutos. Si queres ir directo al combate, ya tenes el boton para entrar a la primera pelea.</p>
          </div>
          <div class="hero-actions compact">
            ${button("Jugar FTUE", "continue-story")}
            ${button("Ir a la pelea", "jump-first-fight", "ghost")}
          </div>
        </div>
        <div class="mission-grid">
          ${this.data.missions
            .map((mission) => {
              const locked = mission.number > unlockedMission;
              return `
                <article class="mission-card ${locked ? "locked" : ""}">
                  <img src="${this.data.arenasById[mission.arena_id].backgroundUrl}" alt="${mission.title}" />
                  <div class="mission-copy">
                    <span class="eyebrow">MISION ${mission.number}</span>
                    <h3>${mission.title}</h3>
                    <p>${mission.summary}</p>
                    <div class="pill-row">
                      <span class="pill">${mission.fights.length} pelea(s)</span>
                      ${mission.ftue ? '<span class="pill accent">FTUE 2 MIN</span>' : ""}
                    </div>
                    ${button(locked ? "Bloqueada" : "Jugar", "play-mission", locked ? "disabled" : "")}
                  </div>
                </article>
              `;
            })
            .join("")}
        </div>
      </section>
    `;
    this.stage.querySelectorAll('[data-action="play-mission"]').forEach((node, index) => {
      if (node.classList.contains("disabled")) return;
      node.addEventListener("click", () => {
        this.audio?.playEffect("uiTap");
        this.startStoryMission(this.data.missions[index]);
      });
    });
    this.bindActions({
      back: () => this.go("menu"),
      "continue-story": () => this.startStoryMission(this.data.missions[Math.max(0, unlockedMission - 1)]),
      "jump-first-fight": () => this.launchFirstFight(),
    });
  }

  async renderOnlineMenu() {
    const renderId = this.renderVersion;
    const background = this.themeUrl("menu_online_bg.png");
    const onlineStep = this.sceneParams.onlineStep || "setup";
    const rankingRange = this.sceneParams.rankingRange || "global";
    const rankingView = this.sceneParams.rankingView || "general";
    const { authMode, rememberAuth } = this.authSceneState();
    const clans = this.data.clans;
    const weapons = this.data.onlineWeapons;
    const activeUsername = (this.onlineProfile.username || this.auth.user?.username || "").trim();
    const activeClanId = this.onlineProfile.clan_id || clans[0]?.id || "cuervo_negro";

    if (!this.auth.token) {
      this.stage.innerHTML = `
        <section class="scene auth-scene scene-backdrop" style="--scene-image: url('${background}')">
          <div class="scene-overlay"></div>
          <div class="auth-card">
            <div class="scene-header tight">
              <h2>Modo online</h2>
            </div>
            <p>Necesitas una cuenta para crear o unirte a una sala Socket.IO.</p>
            <div class="auth-switch-row">
              <button type="button" class="pill-button ${authMode === "login" ? "active" : ""}" data-action="show-login">Iniciar sesion</button>
              <button type="button" class="pill-button ${authMode === "register" ? "active" : ""}" data-action="show-register">Registrarse</button>
            </div>
            ${
              authMode === "login"
                ? `
                  <form id="login-form" class="stack-form">
                    <input name="identity" autocomplete="username" placeholder="Usuario o mail" value="${this.onlineProfile.username || ""}" />
                    <input name="password" type="password" autocomplete="current-password" placeholder="Contrasena" />
                    <div class="auth-remember-row">
                      <button type="button" class="pill-button ${rememberAuth ? "active" : ""}" data-action="toggle-remember">Recordar contrasena ${rememberAuth ? "SI" : "NO"}</button>
                      <span class="helper compact">Guarda el acceso en este dispositivo.</span>
                    </div>
                    <div class="form-actions">
                      ${button("Entrar", "login")}
                      ${button("Volver", "back", "ghost")}
                    </div>
                  </form>
                `
                : `
                  <form id="register-form" class="stack-form">
                    <input name="username" autocomplete="username" placeholder="Nombre de usuario" value="${this.onlineProfile.username || ""}" />
                    <input name="email" type="email" autocomplete="email" placeholder="Mail" />
                    <input name="password" type="password" autocomplete="new-password" inputmode="numeric" minlength="8" maxlength="8" pattern="[0-9]{8}" placeholder="Contrasena (8 digitos)" />
                    <div class="auth-remember-row">
                      <button type="button" class="pill-button ${rememberAuth ? "active" : ""}" data-action="toggle-remember">Recordar contrasena ${rememberAuth ? "SI" : "NO"}</button>
                      <span class="helper compact">Se mantiene la sesion en este equipo.</span>
                    </div>
                    <div class="form-actions">
                      ${button("Crear cuenta", "register")}
                      ${button("Volver", "back", "ghost")}
                    </div>
                  </form>
                `
            }
          </div>
        </section>
      `;
      this.stage.querySelector('[data-action="login"]')?.addEventListener("click", async (event) => {
        event.preventDefault();
        this.audio?.playEffect("uiTap");
        const form = this.stage.querySelector("#login-form");
        if (!form) return;
        const ok = await this.submitAuthLogin(form, rememberAuth);
        if (ok) this.go("online", { onlineStep: "clan-entry" });
      });
      this.stage.querySelector('[data-action="register"]')?.addEventListener("click", async (event) => {
        event.preventDefault();
        this.audio?.playEffect("uiTap");
        const form = this.stage.querySelector("#register-form");
        if (!form) return;
        const ok = await this.submitAuthRegister(form, rememberAuth);
        if (ok) this.go("online", { onlineStep: "clan-entry" });
      });
      this.bindActions({
        back: () => this.go("menu"),
        "show-login": () => this.go("online", { authMode: "login", rememberAuth, onlineStep: "clan-entry" }),
        "show-register": () => this.go("online", { authMode: "register", rememberAuth, onlineStep: "clan-entry" }),
        "toggle-remember": () => this.go("online", { authMode, rememberAuth: !rememberAuth, onlineStep: "clan-entry" }),
      });
      return;
    }

    if (onlineStep === "clan-entry") {
      this.stage.innerHTML = `
        <section class="scene card-scene scene-backdrop" style="--scene-image: url('${background}')">
          <div class="scene-overlay"></div>
          <div class="scene-header">
            <div>
              <h2>Online</h2>
              <p class="helper">Elegi uno de los 4 clanes para entrar al modo online.</p>
            </div>
            <div class="inline-actions">
              ${button("Cerrar sesion", "logout", "ghost")}
              ${button("Volver", "back", "ghost")}
            </div>
          </div>
          <div class="card online-entry-card">
            <div class="clan-entry-grid">
              ${clans
                .map(
                  (clan) => `
                    <button type="button" class="select-card clan-entry-card ${clan.id === activeClanId ? "active" : ""}" data-action="choose-online-clan" data-value="${clan.id}">
                      <img src="${clan.portrait}" alt="${clan.name}" />
                      <div class="clan-entry-copy">
                        <span class="eyebrow">Clan</span>
                        <strong>${clan.name}</strong>
                        <span>Entrar con este guerrero</span>
                      </div>
                    </button>
                  `,
                )
                .join("")}
            </div>
          </div>
        </section>
      `;
      this.bindActions({
        back: () => this.go("menu"),
        logout: () => {
          clearAuth();
          this.auth = loadAuth();
          this.rememberAuth = false;
          this.realtime.disconnect();
          this.go("menu");
        },
        "choose-online-clan": (event) => {
          this.onlineProfile.clan_id = event.currentTarget.dataset.value;
          const clan = clans.find((item) => item.id === this.onlineProfile.clan_id);
          this.onlineProfile.color = clan?.color || [170, 48, 52];
          saveOnlineProfile(this.onlineProfile);
          this.go("online", { onlineStep: "setup", rankingRange, rankingView });
        },
      });
      return;
    }

    try {
      const [rooms, ranking, clanRanking, rankingSummary] = await Promise.all([
        this.api.rooms(),
        this.api.ranking(rankingRange),
        this.api.clanRanking(rankingRange),
        this.api.rankingSummary(rankingRange, activeUsername, activeClanId),
      ]);
      if (renderId !== this.renderVersion || this.scene !== "online") return;
      this.onlineLists = { rooms, ranking, clanRanking, rankingSummary };
    } catch (_error) {
      this.onlineLists = { rooms: [], ranking: [], clanRanking: [], rankingSummary: null };
    }

    const clanById = Object.fromEntries(clans.map((clan) => [clan.id, clan]));
    const selectedClan = clanById[this.onlineProfile.clan_id] || clans[0];
    const selectedWeapon = weapons.find((weapon) => weapon.id === this.onlineProfile.weapon_id) || weapons[0];
    const rangeMeta = this.rankingRangeMeta(rankingRange);
    const rankingSummary = this.onlineLists.rankingSummary || {};
    const summaryPlayer = rankingSummary.player || null;
    const summaryClan = rankingSummary.clan || null;
    const emptyPeriodText =
      rankingRange === "global"
        ? "Juga al menos una pelea online para aparecer en el ranking."
        : "Todavia no hay actividad suficiente en este periodo.";
    const activeUsernameKey = activeUsername.toLowerCase();
    const generalRankingMarkup = this.onlineLists.ranking.length
      ? this.onlineLists.ranking
          .map((row, index) => {
            const clan = clanById[row.clan];
            const clanName = clan?.name || row.clan || "Clan";
            const isCurrentPlayer = String(row.username || "").toLowerCase() === activeUsernameKey;
            return `<div class="list-row rank-row ${isCurrentPlayer ? "focus" : ""}"><span>#${index + 1} ${row.username}${isCurrentPlayer ? " · vos" : ""}</span><span>${row.points} pts · ${row.wins || 0}V/${row.losses || 0}D · ${clanName}</span></div>`;
          })
          .join("")
      : "<div class='list-row'>Sin ranking general disponible.</div>";
    const clanRankingMarkup = this.onlineLists.clanRanking.length
      ? this.onlineLists.clanRanking
          .map((row, index) => {
            const clan = clanById[row.clan];
            const clanName = clan?.name || row.clan || "Clan";
            const isSelectedClan = row.clan === selectedClan?.id;
            return `<div class="list-row rank-row ${isSelectedClan ? "focus" : ""}"><span>#${index + 1} ${clanName}${isSelectedClan ? " · mi clan" : ""}</span><span>${row.points} pts · ${row.wins}V/${row.losses}D · ${row.members} jugadores</span></div>`;
          })
          .join("")
      : "<div class='list-row'>Sin ranking por clan disponible.</div>";
    const myClanMarkup = `
      <div class="focus-grid">
        <article class="focus-card">
          <span class="eyebrow">TU POSICION GENERAL</span>
          <h3>${summaryPlayer?.username || activeUsername || "Jugador actual"}</h3>
          <div class="focus-rank">${summaryPlayer?.position ? `#${summaryPlayer.position}` : "--"}</div>
          <p>${summaryPlayer?.position ? `Puesto ${summaryPlayer.position} de ${summaryPlayer.totalPlayers || 0} jugadores.` : emptyPeriodText}</p>
          <div class="pill-row">
            <span class="pill accent">${summaryPlayer?.points || 0} pts</span>
            <span class="pill">${summaryPlayer?.wins || 0}V / ${summaryPlayer?.losses || 0}D</span>
          </div>
        </article>
        <article class="focus-card">
          <span class="eyebrow">POSICION DEL CLAN</span>
          <h3>${selectedClan?.name || "Clan"}</h3>
          <div class="focus-rank">${summaryClan?.position ? `#${summaryClan.position}` : "--"}</div>
          <p>${summaryClan?.position ? `Puesto ${summaryClan.position} de ${summaryClan.totalClans || 0} clanes.` : emptyPeriodText}</p>
          <div class="pill-row">
            <span class="pill accent">${summaryClan?.points || 0} pts</span>
            <span class="pill">${summaryClan?.wins || 0}V / ${summaryClan?.losses || 0}D · ${summaryClan?.members || 0} miembros</span>
          </div>
        </article>
      </div>
      <div class="list-panel compact-list">
        <div class="list-row focus-inline-row">
          <span>Rango activo</span>
          <strong>${rangeMeta.title}</strong>
        </div>
        <div class="list-row focus-inline-row">
          <span>Alias activo</span>
          <strong>${activeUsername || "Jugador actual"}</strong>
        </div>
      </div>
    `;
    this.stage.innerHTML = `
      <section class="scene online-scene scene-backdrop" style="--scene-image: url('${background}')">
        <div class="scene-overlay"></div>
        <div class="scene-header">
          <h2>Online</h2>
          <div class="inline-actions">
            ${button("Cerrar sesion", "logout", "ghost")}
            ${button("Volver", "back", "ghost")}
          </div>
        </div>
        <div class="online-grid">
          <div class="card">
            <h3>Tu combatiente online</h3>
            <label>Alias</label>
            <input id="online-username" value="${this.onlineProfile.username || this.auth.user?.username || ""}" />
            <label>Arma</label>
            <div class="weapon-grid">
              ${weapons
                .map(
                  (weapon) => `
                    <button type="button" class="pill-button ${weapon.id === this.onlineProfile.weapon_id ? "active" : ""}" data-action="pick-weapon" data-value="${weapon.id}">
                      ${weapon.name}
                    </button>
                  `,
                )
                .join("")}
            </div>
            <div class="online-preview-card">
              <img src="${selectedClan?.portrait || ""}" alt="${selectedClan?.name || "Clan"}" />
              <div class="online-preview-copy">
                <span class="eyebrow">Combatiente activo</span>
                <h3>${selectedClan?.name || "Clan"}</h3>
                <p>${selectedWeapon?.name || "Katana"} - ${this.auth.user ? this.auth.user.username : this.onlineProfile.username || "guerrero"}</p>
                <div class="inline-actions">
                  ${button("Cambiar clan", "change-clan", "ghost")}
                </div>
              </div>
            </div>
            <label>Codigo sala</label>
            <input id="room-code" placeholder="ABCD12" />
            <div class="form-actions">
              ${button("Crear sala", "create-room")}
              ${button("Unirme", "join-room")}
            </div>
          </div>
          <div class="card ranking-card">
            <h3>Salas</h3>
            <div class="list-panel">
              ${this.onlineLists.rooms.length ? this.onlineLists.rooms.map((room) => `<div class="list-row">${room.roomCode} - ${room.status}</div>`).join("") : "<div class='list-row'>No hay salas publicas visibles.</div>"}
            </div>
            <div class="ranking-toolbar">
              <div>
                <h3>Rankings online</h3>
                <p class="helper">${rangeMeta.subtitle}</p>
              </div>
              <div class="ranking-filters">
                ${rankingFilterButton("Hoy", "today", rankingRange)}
                ${rankingFilterButton("Semana", "week", rankingRange)}
                ${rankingFilterButton("Global", "global", rankingRange)}
              </div>
            </div>
            <div class="ranking-tabs">
              ${rankingViewButton("General", "general", rankingView)}
              ${rankingViewButton("Clanes", "clans", rankingView)}
              ${rankingViewButton("Mi clan", "my-clan", rankingView)}
            </div>
            ${rankingView === "general" ? `<h3>Ranking general · ${rangeMeta.title}</h3><div class="list-panel ranking-list">${generalRankingMarkup}</div>` : ""}
            ${rankingView === "clans" ? `<h3>Ranking por clan · ${rangeMeta.title}</h3><div class="list-panel ranking-list">${clanRankingMarkup}</div>` : ""}
            ${rankingView === "my-clan" ? `<div class="ranking-focus"><h3>Mi clan · ${rangeMeta.title}</h3>${myClanMarkup}</div>` : ""}
          </div>
        </div>
      </section>
    `;
    this.bindActions({
      back: () => this.go("menu"),
      logout: () => {
        clearAuth();
        this.auth = loadAuth();
        this.rememberAuth = false;
        this.realtime.disconnect();
        this.go("menu");
      },
      "change-clan": () => this.go("online", { onlineStep: "clan-entry", rankingRange, rankingView }),
      "pick-weapon": (event) => {
        this.onlineProfile.weapon_id = event.currentTarget.dataset.value;
        saveOnlineProfile(this.onlineProfile);
        this.go("online", { onlineStep: "setup", rankingRange, rankingView });
      },
      "set-ranking-range": (event) => this.go("online", { onlineStep: "setup", rankingRange: event.currentTarget.dataset.value, rankingView }),
      "set-ranking-view": (event) => this.go("online", { onlineStep: "setup", rankingRange, rankingView: event.currentTarget.dataset.value }),
      "create-room": () => this.createRoom(),
      "join-room": () => this.joinRoom(),
    });
  }

  renderLobby(snapshot, statusText) {
    this.stage.innerHTML = `
      <section class="scene auth-scene scene-backdrop" style="--scene-image: url('${this.themeUrl("menu_online_bg.png")}')">
        <div class="scene-overlay"></div>
        <div class="auth-card">
          <div class="scene-header tight">
            <h2>Sala ${snapshot.roomCode}</h2>
          </div>
          <p>${statusText}</p>
          <div class="list-panel">
            ${(snapshot.players || [])
              .map(
                (player) => `
                  <div class="list-row">
                    <strong>${player.username}</strong>
                    <span>${player.clanName || player.fighterName || "Guerrero"}</span>
                  </div>
                `,
              )
              .join("")}
          </div>
          <div class="form-actions">
            ${button("Salir", "leave-room", "ghost")}
          </div>
        </div>
      </section>
    `;
    this.bindActions({
      "leave-room": () => {
        this.realtime.leaveRoom();
        this.realtime.disconnect();
        this.go("online", { onlineStep: "setup" });
      },
    });
  }

  renderOptions() {
    this.stage.innerHTML = `
      <section class="scene card-scene scene-backdrop" style="--scene-image: url('${this.themeUrl("menu_armory_bg.png")}')">
        <div class="scene-overlay"></div>
        <div class="scene-header">
          <h2>Opciones</h2>
          <div class="inline-actions">
            ${button("Volver", "back", "ghost")}
          </div>
        </div>
        <div class="online-grid">
          <div class="card">
            <h3>Audio</h3>
            <div class="audio-panel audio-stack">
              <div>
                <span class="eyebrow">MUSICA DEL MENU</span>
                <p>${this.settings.musicMuted ? "La musica del menu esta apagada." : "La musica del menu esta activa."}</p>
              </div>
              ${this.renderAudioToggle("toggle-music", "MUSICA", !this.settings.musicMuted, "large")}
            </div>
            <div class="audio-panel audio-stack">
              <div>
                <span class="eyebrow">EFECTOS Y GOLPES</span>
                <p>${this.settings.fxMuted ? "Los golpes, botones y efectos estan apagados." : "Los golpes, botones y efectos estan activos."}</p>
              </div>
              ${this.renderAudioToggle("toggle-fx", "EFECTOS", !this.settings.fxMuted, "large")}
            </div>
            <p class="helper">Los botones ahora tienen un sonido minimo y los golpes usan el canal de efectos.</p>
          </div>
          <div class="card">
            <h3>Controles</h3>
            <div class="control-columns">
              <div class="control-card">
                <span class="eyebrow">PC</span>
                <div class="list-panel">
                  <div class="list-row">Mover: A / D</div>
                  <div class="list-row">Saltar: W</div>
                  <div class="list-row">Agacharse: S</div>
                  <div class="list-row">Golpe: J</div>
                  <div class="list-row">S + J: patada baja</div>
                  <div class="list-row">Aire + J: voladora</div>
                  <div class="list-row">Bloqueo: I</div>
                  <div class="list-row">Dash: L</div>
                  <div class="list-row">Especial: K</div>
                  <div class="list-row">Pausa: ESC</div>
                </div>
              </div>
              <div class="control-card">
                <span class="eyebrow">ANDROID</span>
                <div class="list-panel">
                  <div class="list-row">Mover: IZQ / DER</div>
                  <div class="list-row">Saltar: SALTO</div>
                  <div class="list-row">Agacharse: ABAJO</div>
                  <div class="list-row">Golpe: GOLPE</div>
                  <div class="list-row">ABAJO + GOLPE: patada baja</div>
                  <div class="list-row">AIRE + GOLPE: voladora</div>
                  <div class="list-row">Bloqueo: BLOQ</div>
                  <div class="list-row">Dash: DASH</div>
                  <div class="list-row">Especial: ESPECIAL</div>
                  <div class="list-row">Pausa: boton II</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    `;
    this.bindActions({
      "toggle-music": () => this.toggleMusic(),
      "toggle-fx": () => this.toggleFx(),
      back: () => this.go("menu"),
    });
  }

  mountBattle() {
    const params = this.sceneParams;
    const arena = this.data.arenasById[params.arenaId];
    if (params.mode === "quick") {
      const player = this.data.fightersById[params.fighterId];
      const enemy = this.data.fightersById[params.enemyId];
      this.battle = new BattleView({
        app: this,
        container: this.stage,
        mode: "quick",
        arena,
        player,
        enemy,
        playerWeapon: this.data.weaponsById.katana,
        enemyWeapon: this.data.weaponsById.katana,
        audio: this.audio,
        onExit: () => this.go("menu"),
        onRetry: () => this.go("battle", params),
        onMatchEnd: () => {},
      });
      this.battle.mount();
      return;
    }

    if (params.mode === "story") {
      const mission = params.mission;
      const fightIndex = params.fightIndex || 0;
      const enemy = this.data.enemiesById[mission.fights[fightIndex]];
      this.battle = new BattleView({
        app: this,
        container: this.stage,
        mode: "story",
        arena,
        player: this.data.storyFighter,
        enemy,
        playerWeapon: this.data.weaponsById.katana,
        enemyWeapon: this.data.weaponsById.katana,
        audio: this.audio,
        storyHints:
          mission.number === 1
            ? [
                { text: "Movete con A/D o con IZQ y DER", duration: 2500, gap: 900 },
                { text: "Usa SALTO y ABAJO para moverte mejor", duration: 2300, gap: 900 },
                { text: "GOLPE hace patada baja agachado y voladora en el aire", duration: 3000, gap: 900 },
                { text: "Bloquea con BLOQ y usa DASH para esquivar", duration: 2600, gap: 900 },
              ]
            : [],
        onExit: (playerWon) => this.finishStoryBattle(playerWon, mission, fightIndex),
        onRetry: () => this.go("battle", params),
        onMatchEnd: () => {},
      });
      this.battle.mount();
      return;
    }

    if (params.mode === "online") {
      const localMeta = params.match.players.find((item) => item.socketId === this.realtime.state.socketId) || params.match.players[0];
      const enemyMeta = params.match.players.find((item) => item.socketId !== this.realtime.state.socketId) || params.match.players[1];
      const playerWeapon = this.data.weaponsById[localMeta.weaponId] || this.data.onlineWeapons[0];
      const enemyWeapon = this.data.weaponsById[enemyMeta.weaponId] || this.data.onlineWeapons[0];
      this.battle = new BattleView({
        app: this,
        container: this.stage,
        mode: "online",
        arena,
        player: {
          ...localMeta,
          id: localMeta.clanId,
          name: localMeta.username,
          portrait: this.data.assetUrl(localMeta.portrait),
          portraitUrl: this.data.assetUrl(localMeta.portrait),
          spriteUrl: this.data.assetUrl(localMeta.spriteSheet),
          maxHealth: localMeta.maxHealth,
          maxStamina: localMeta.maxStamina,
          attackPower: localMeta.attackPower,
        },
        enemy: {
          ...enemyMeta,
          id: enemyMeta.clanId,
          name: enemyMeta.username,
          portrait: this.data.assetUrl(enemyMeta.portrait),
          portraitUrl: this.data.assetUrl(enemyMeta.portrait),
          spriteUrl: this.data.assetUrl(enemyMeta.spriteSheet),
          maxHealth: enemyMeta.maxHealth,
          maxStamina: enemyMeta.maxStamina,
          attackPower: enemyMeta.attackPower,
        },
        playerWeapon,
        enemyWeapon,
        realtime: this.realtime,
        audio: this.audio,
        currentRound: params.match.currentRound || 1,
        onlineSocketId: this.realtime.state.socketId,
        onExit: () => {
          this.realtime.leaveRoom();
          this.realtime.disconnect();
          this.go("online");
        },
        onMatchEnd: () => {},
      });
      this.battle.player.socketId = localMeta.socketId;
      this.battle.enemy.socketId = enemyMeta.socketId;
      this.battle.mount();
    }
  }

  async finishStoryBattle(playerWon, mission, fightIndex) {
    if (!playerWon) {
      this.toast("Kenji cayo. Reintenta la mision.");
      this.go("story");
      return;
    }
    if (fightIndex + 1 < mission.fights.length) {
      this.go("battle", {
        mode: "story",
        mission,
        arenaId: mission.arena_id,
        fightIndex: fightIndex + 1,
      });
      return;
    }

    if (mission.number === 1) {
      this.progress = {
        ...this.progress,
        ...buildCompletedMissionProgress(1),
      };
    } else {
      this.progress.story_mission = Math.max(this.progress.story_mission, mission.number);
      this.progress.first_time_completed = this.progress.story_mission >= 1;
      this.progress.unlocked_modes = unique([...(this.progress.unlocked_modes || []), "Historia", "Juego rapido", "Online"]);
    }
    saveProgress(this.progress);

    if (this.auth.token) {
      try {
        const payload = await this.api.updateProgress(
          {
            first_time_completed: this.progress.first_time_completed,
            story_act: this.progress.story_act,
            story_mission: this.progress.story_mission,
            unlocked_modes: this.progress.unlocked_modes,
          },
          this.onlineProfile,
        );
        if (payload?.user) {
          this.auth.user = payload.user;
          if (this.rememberAuth) {
            saveAuth(this.auth);
          }
        }
      } catch (_error) {}
    }

    const cutscene = this.data.cutscenesById[mission.outro_cutscene];
    if (cutscene) {
      this.playCutscene(cutscene, () => this.go("menu"));
      return;
    }
    this.go("menu");
  }

  launchFirstFight() {
    const mission = this.data.missions[0];
    this.go("battle", {
      mode: "story",
      mission,
      arenaId: mission.arena_id,
      fightIndex: 0,
    });
  }

  startStoryMission(mission) {
    const cutscene = this.data.cutscenesById[mission.intro_cutscene];
    if (cutscene) {
      this.playCutscene(cutscene, () =>
        this.go("battle", {
          mode: "story",
          mission,
          arenaId: mission.arena_id,
          fightIndex: 0,
        }),
      );
      return;
    }
    this.go("battle", { mode: "story", mission, arenaId: mission.arena_id, fightIndex: 0 });
  }

  playCutscene(cutscene, onComplete) {
    this.audio.setScene("cutscene");
    const panels = [...(cutscene.panels || [])];
    let index = 0;
    const renderPanel = () => {
      const panel = panels[index];
      if (!panel) {
        onComplete();
        return;
      }
      this.stage.innerHTML = `
        <section class="scene cutscene-scene scene-backdrop" style="--scene-image: url('${this.themeUrl("menu_main_bg_v2.png")}')">
          <div class="scene-overlay"></div>
          <img class="cutscene-image" src="${this.data.assetUrl(panel.image)}" alt="${panel.speaker}" />
          <div class="cutscene-panel">
            <div class="scene-header tight">
              <span class="eyebrow">${panel.speaker}</span>
            </div>
            <p>${panel.text}</p>
            <div class="form-actions">
              ${button(index + 1 >= panels.length ? "Seguir" : "Siguiente", "next-panel")}
              ${button("Saltar", "skip-panel", "ghost")}
            </div>
          </div>
        </section>
      `;
      this.bindActions({
        "next-panel": () => {
          index += 1;
          renderPanel();
        },
        "skip-panel": () => onComplete(),
      });
    };
    renderPanel();
  }

  startOnlineBattle(match) {
    this.go("battle", {
      mode: "online",
      match,
      arenaId: match.arenaId,
    });
  }

  buildOnlinePayload() {
    const clan = this.data.clans.find((item) => item.id === this.onlineProfile.clan_id) || this.data.clans[0];
    const weapon = this.data.weaponsById[this.onlineProfile.weapon_id] || this.data.onlineWeapons[0];
    const username = this.stage.querySelector("#online-username")?.value?.trim() || this.auth.user?.username || "player";
    this.onlineProfile.username = username;
    this.onlineProfile.color = clan?.color || this.onlineProfile.color;
    saveOnlineProfile(this.onlineProfile);
    return {
      platform: "android",
      arenaId: "coliseo_de_acero",
      onlineFighter: {
        username,
        clan_id: clan.id,
        clan_name: clan.name,
        weapon_id: weapon.id,
        weapon_name: weapon.name,
        color: this.onlineProfile.color,
        max_health: this.data.onlineFighters.base.max_health,
        max_stamina: this.data.onlineFighters.base.max_stamina,
        speed: this.data.onlineFighters.base.speed + (weapon.bonuses?.speed || 0),
        attack_power: this.data.onlineFighters.base.attack_power + (weapon.bonuses?.attack_power || 0),
        defense: this.data.onlineFighters.base.defense + (weapon.bonuses?.defense || 0),
        range: weapon.range,
      },
    };
  }

  createRoom() {
    try {
      this.realtime.connect();
      this.realtime.createRoom(this.buildOnlinePayload());
    } catch (error) {
      this.toast(error.message);
    }
  }

  joinRoom() {
    const roomCode = this.stage.querySelector("#room-code")?.value?.trim().toUpperCase();
    if (!roomCode) {
      this.toast("Ingresa un codigo de sala.");
      return;
    }
    try {
      this.realtime.connect();
      this.realtime.joinRoom({ roomCode, ...this.buildOnlinePayload() });
    } catch (error) {
      this.toast(error.message);
    }
  }

  bindActions(handlers) {
    Object.entries(handlers).forEach(([action, handler]) => {
      this.stage.querySelectorAll(`[data-action="${action}"]`).forEach((node) => {
        node.addEventListener("click", (event) => {
          this.audio?.playEffect("uiTap");
          handler(event);
        });
      });
    });
  }

  toast(message) {
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2400);
  }
}


