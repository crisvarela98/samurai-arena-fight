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

export class SamuraiArenaWebApp {
  constructor(root, data) {
    this.root = root;
    this.data = data;
    this.settings = loadSettings();
    this.progress = loadProgress();
    this.auth = loadAuth();
    this.onlineProfile = loadOnlineProfile();
    this.runtimeConfig = resolveRuntimeConfig(this.settings);
    this.api = new ApiClient(() => this.runtimeConfig, () => this.auth.token);
    this.realtime = new RealtimeClient(() => this.runtimeConfig, () => this.auth.token);
    this.audio = new WebAudioManager(this.settings, data.assetUrl);
    this.scene = "splash";
    this.sceneParams = {};
    this.battle = null;
    this.roomSnapshot = null;
    this.onlineLists = { rooms: [], ranking: [], clanRanking: [] };
    this.renderVersion = 0;
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
      }
    }
    setTimeout(() => this.go("menu"), 2000);
  }

  themeUrl(fileName) {
    return this.data.assetUrl(`assets/ui/${fileName}`);
  }

  renderSoundToggle(size = "") {
    return `<button type="button" class="sound-toggle ${size}" data-action="toggle-sound"><span class="sound-indicator ${this.settings.musicMuted ? "off" : "on"}"></span>${this.settings.musicMuted ? "AUDIO OFF" : "AUDIO ON"}</button>`;
  }

  syncSettings() {
    saveSettings(this.settings);
    this.runtimeConfig = resolveRuntimeConfig(this.settings);
    this.audio.setSettings(this.settings);
  }

  toggleSound() {
    const next = this.audio.toggleAll();
    this.settings.musicMuted = next.musicMuted;
    this.settings.fxMuted = next.fxMuted;
    this.syncSettings();
    this.renderFrame();
  }

  go(scene, params = {}) {
    if (this.battle) {
      this.battle.destroy();
      this.battle = null;
    }
    this.scene = scene;
    this.sceneParams = params;
    this.audio.setScene(scene);
    this.renderFrame();
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
    this.stage.innerHTML = `
      <section class="scene menu-scene scene-backdrop" style="--scene-image: url('${this.themeUrl("menu_main_bg_v2.png")}')">
        <div class="scene-overlay scene-overlay-right"></div>
        <div class="scene-topbar">
          <div class="topbar-copy">
            <span class="eyebrow">ACTO 1 - EL DESPERTAR</span>
            <span class="topbar-note">Menu clasico, samurai destacado y acceso rapido a la historia</span>
          </div>
          <div class="topbar-actions">
            ${this.renderSoundToggle()}
          </div>
        </div>

        <div class="menu-stage-copy">
          <span class="eyebrow">SAMURAI ARENA FIGHT</span>
          <h1>Kenji vuelve a la arena</h1>
          <p>Vuelve el estilo vintage del menu. El panel derecho concentra las opciones y el samurai vuelve a dominar el resto de la pantalla.</p>
          <div class="menu-badges">
            <span class="pill accent">ANDROID</span>
            <span class="pill">LANDSCAPE</span>
            <span class="pill">${this.auth.user ? `SESION ${this.auth.user.username}` : "SIN SESION"}</span>
          </div>
        </div>

        <div class="vintage-menu-panel">
          <span class="eyebrow">MENU PRINCIPAL</span>
          <h2>Elegi tu camino</h2>
          <div class="menu-actions vertical">
            ${button("Juego rapido", "quick")}
            ${button("Modo historia", "story")}
            ${button("Online", "online", canOnline ? "" : "disabled")}
            ${button("Opciones", "options")}
          </div>
          <div class="status-row">
            <span class="pill">API ${this.runtimeConfig.apiBaseUrl}</span>
            <span class="pill">Historia -> primera pelea</span>
          </div>
        </div>
      </section>
    `;
    this.bindActions({
      "toggle-sound": () => this.toggleSound(),
      quick: () => this.go("quick"),
      story: () => this.go("story"),
      online: () => {
        if (!canOnline) {
          this.toast("Termina la mision 1 para desbloquear Online.");
          return;
        }
        this.go("online");
      },
      options: () => this.go("options"),
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
            ${this.renderSoundToggle()}
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
      "toggle-sound": () => this.toggleSound(),
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
            ${this.renderSoundToggle()}
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
      node.addEventListener("click", () => this.startStoryMission(this.data.missions[index]));
    });
    this.bindActions({
      "toggle-sound": () => this.toggleSound(),
      back: () => this.go("menu"),
      "continue-story": () => this.startStoryMission(this.data.missions[Math.max(0, unlockedMission - 1)]),
      "jump-first-fight": () => this.launchFirstFight(),
    });
  }

  async renderOnlineMenu() {
    const renderId = this.renderVersion;
    const background = this.themeUrl("menu_online_bg.png");

    if (!this.auth.token) {
      this.stage.innerHTML = `
        <section class="scene auth-scene scene-backdrop" style="--scene-image: url('${background}')">
          <div class="scene-overlay"></div>
          <div class="auth-card">
            <div class="scene-header tight">
              <h2>Modo online</h2>
              ${this.renderSoundToggle()}
            </div>
            <p>Necesitas una cuenta para crear o unirte a una sala Socket.IO.</p>
            <form id="login-form" class="stack-form">
              <input name="identity" placeholder="Usuario o email" value="${this.onlineProfile.username || ""}" />
              <input name="password" type="password" placeholder="Contrasena" />
              <div class="form-actions">
                ${button("Entrar", "login")}
                ${button("Volver", "back", "ghost")}
              </div>
            </form>
            <div class="divider"></div>
            <form id="register-form" class="stack-form">
              <input name="username" placeholder="Usuario" value="${this.onlineProfile.username || ""}" />
              <input name="email" type="email" placeholder="Email" />
              <input name="password" type="password" placeholder="Contrasena" />
              ${button("Crear cuenta", "register")}
            </form>
          </div>
        </section>
      `;
      this.stage.querySelector('[data-action="login"]').addEventListener("click", async (event) => {
        event.preventDefault();
        const form = this.stage.querySelector("#login-form");
        const payload = new FormData(form);
        try {
          const result = await this.api.login(payload.get("identity"), payload.get("password"));
          this.auth = result;
          saveAuth(this.auth);
          this.onlineProfile.username = result.user.username;
          saveOnlineProfile(this.onlineProfile);
          this.go("online");
        } catch (error) {
          this.toast(error.message);
        }
      });
      this.stage.querySelector('[data-action="register"]').addEventListener("click", async (event) => {
        event.preventDefault();
        const form = this.stage.querySelector("#register-form");
        const payload = new FormData(form);
        try {
          const result = await this.api.register(payload.get("username"), payload.get("email"), payload.get("password"));
          this.auth = result;
          saveAuth(this.auth);
          this.onlineProfile.username = result.user.username;
          saveOnlineProfile(this.onlineProfile);
          this.go("online");
        } catch (error) {
          this.toast(error.message);
        }
      });
      this.bindActions({
        "toggle-sound": () => this.toggleSound(),
        back: () => this.go("menu"),
      });
      return;
    }

    try {
      const [rooms, ranking, clanRanking] = await Promise.all([this.api.rooms(), this.api.ranking(), this.api.clanRanking()]);
      if (renderId !== this.renderVersion || this.scene !== "online") return;
      this.onlineLists = { rooms, ranking, clanRanking };
    } catch (_error) {
      this.onlineLists = { rooms: [], ranking: [], clanRanking: [] };
    }

    const clans = this.data.clans;
    const weapons = this.data.onlineWeapons;
    const clanById = Object.fromEntries(clans.map((clan) => [clan.id, clan]));
    this.stage.innerHTML = `
      <section class="scene online-scene scene-backdrop" style="--scene-image: url('${background}')">
        <div class="scene-overlay"></div>
        <div class="scene-header">
          <h2>Online</h2>
          <div class="inline-actions">
            ${this.renderSoundToggle()}
            ${button("Cerrar sesion", "logout", "ghost")}
            ${button("Volver", "back", "ghost")}
          </div>
        </div>
        <div class="online-grid">
          <div class="card">
            <h3>Tu combatiente online</h3>
            <label>Alias</label>
            <input id="online-username" value="${this.onlineProfile.username || this.auth.user?.username || ""}" />
            <label>Clan</label>
            <div class="selector-list compact">
              ${clans
                .map(
                  (clan) => `
                    <button type="button" class="select-card ${clan.id === this.onlineProfile.clan_id ? "active" : ""}" data-action="pick-clan" data-value="${clan.id}">
                      <img src="${clan.portrait}" alt="${clan.name}" />
                      <span>${clan.name}</span>
                    </button>
                  `,
                )
                .join("")}
            </div>
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
            <label>Codigo sala</label>
            <input id="room-code" placeholder="ABCD12" />
            <div class="form-actions">
              ${button("Crear sala", "create-room")}
              ${button("Unirme", "join-room")}
            </div>
          </div>
          <div class="card">
            <h3>Salas</h3>
            <div class="list-panel">
              ${this.onlineLists.rooms.length ? this.onlineLists.rooms.map((room) => `<div class="list-row">${room.roomCode} - ${room.status}</div>`).join("") : "<div class='list-row'>No hay salas publicas visibles.</div>"}
            </div>
            <h3>Ranking general</h3>
            <div class="list-panel">
              ${this.onlineLists.ranking.length ? this.onlineLists.ranking.map((row, index) => {
                const clan = clanById[row.clan];
                const clanName = clan?.name || row.clan || "Clan";
                return `<div class="list-row">#${index + 1} ${row.username} - ${row.points} pts - ${clanName}</div>`;
              }).join("") : "<div class='list-row'>Sin ranking general disponible.</div>"}
            </div>
            <h3>Ranking por clan</h3>
            <div class="list-panel">
              ${this.onlineLists.clanRanking.length ? this.onlineLists.clanRanking.map((row, index) => {
                const clan = clanById[row.clan];
                const clanName = clan?.name || row.clan || "Clan";
                return `<div class="list-row">#${index + 1} ${clanName} - ${row.points} pts - ${row.wins}V/${row.losses}D - ${row.members} jugadores</div>`;
              }).join("") : "<div class='list-row'>Sin ranking por clan disponible.</div>"}
            </div>
          </div>
        </div>
      </section>
    `;
    this.bindActions({
      "toggle-sound": () => this.toggleSound(),
      back: () => this.go("menu"),
      logout: () => {
        clearAuth();
        this.auth = loadAuth();
        this.realtime.disconnect();
        this.go("menu");
      },
      "pick-clan": (event) => {
        this.onlineProfile.clan_id = event.currentTarget.dataset.value;
        const clan = clans.find((item) => item.id === this.onlineProfile.clan_id);
        this.onlineProfile.color = clan?.color || [170, 48, 52];
        saveOnlineProfile(this.onlineProfile);
        this.go("online");
      },
      "pick-weapon": (event) => {
        this.onlineProfile.weapon_id = event.currentTarget.dataset.value;
        saveOnlineProfile(this.onlineProfile);
        this.go("online");
      },
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
            ${this.renderSoundToggle()}
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
      "toggle-sound": () => this.toggleSound(),
      "leave-room": () => {
        this.realtime.leaveRoom();
        this.realtime.disconnect();
        this.go("online");
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
            ${this.renderSoundToggle()}
            ${button("Volver", "back", "ghost")}
          </div>
        </div>
        <div class="online-grid">
          <div class="card">
            <h3>Audio y conexion</h3>
            <div class="audio-panel">
              <div>
                <span class="eyebrow">SONIDO</span>
                <p>${this.settings.musicMuted ? "El audio esta apagado." : "La musica y los efectos estan activos."}</p>
              </div>
              ${this.renderSoundToggle("large")}
            </div>
            <label>Backend URL</label>
            <input id="server-url" value="${this.settings.serverUrl || this.settings.apiBaseUrl || this.settings.socketUrl || ""}" placeholder="https://samurai-arena-fight.onrender.com" />
            <div class="form-actions">
              ${button("Guardar", "save-options")}
              ${button("Pantalla completa", "fullscreen")}
            </div>
            <p class="helper">En produccion usa la URL HTTPS de Render. Si lo dejas vacio, el cliente intenta usar el mismo origen.</p>
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
      "toggle-sound": () => this.toggleSound(),
      back: () => this.go("menu"),
      "save-options": () => {
        const serverUrl = this.stage.querySelector("#server-url").value.trim();
        this.settings.serverUrl = serverUrl;
        this.settings.apiBaseUrl = serverUrl;
        this.settings.socketUrl = serverUrl;
        this.syncSettings();
        this.toast("Opciones guardadas.");
        this.go("options");
      },
      fullscreen: async () => {
        try {
          if (!document.fullscreenElement) {
            await document.documentElement.requestFullscreen();
          }
          if (screen.orientation?.lock) {
            await screen.orientation.lock("landscape");
          }
        } catch (_error) {
          this.toast("La pantalla completa depende del navegador o del WebView.");
        }
      },
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
                { text: "Golpea con GOLPE, bloquea con BLOQ y usa DASH para esquivar", duration: 3200, gap: 900 },
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
        await this.api.updateProgress(
          {
            first_time_completed: this.progress.first_time_completed,
            story_act: this.progress.story_act,
            story_mission: this.progress.story_mission,
            unlocked_modes: this.progress.unlocked_modes,
          },
          this.onlineProfile,
        );
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
              ${this.renderSoundToggle()}
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
        "toggle-sound": () => this.toggleSound(),
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
        node.addEventListener("click", handler);
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


