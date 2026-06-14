import { resolveRuntimeConfig } from "./config.js";
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
    this.scene = "splash";
    this.sceneParams = {};
    this.battle = null;
    this.roomSnapshot = null;
    this.onlineLists = { rooms: [], ranking: [] };
    this.bindRealtime();
  }

  bindRealtime() {
    this.realtime.on("room_created", (payload) => {
      this.roomSnapshot = payload;
      this.renderLobby(payload, "Esperando rival...");
    });
    this.realtime.on("waiting_for_player", (payload) => {
      this.roomSnapshot = payload;
      this.renderLobby(payload, "Compartí el código y esperá.");
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

  go(scene, params = {}) {
    if (this.battle) {
      this.battle.destroy();
      this.battle = null;
    }
    this.scene = scene;
    this.sceneParams = params;
    this.renderFrame();
  }

  renderFrame() {
    this.root.innerHTML = `<div class="shell"><div class="app-stage"></div></div>`;
    this.stage = this.root.querySelector(".app-stage");
    if (this.scene === "splash") {
      this.stage.innerHTML = `
        <section class="splash-screen">
          <div class="logo-slot">TU LOGO / STUDIO</div>
          <div class="logo-slot game">SAMURAI ARENA FIGHT</div>
        </section>
      `;
      return;
    }
    if (this.scene === "battle") {
      this.mountBattle();
      return;
    }
    this.renderScene();
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
      <section class="scene menu-scene">
        <div class="hero-panel">
          <span class="eyebrow">WEB CLIENT · CANVAS 2D · MOBILE FIRST</span>
          <h1>Samurai Arena Fight</h1>
          <p>Versión web lista para Vercel, Netlify y empaquetado en WebView Android.</p>
          <div class="menu-actions">
            ${button("Juego rápido", "quick")}
            ${button("Modo historia", "story")}
            ${button("Online", "online", canOnline ? "" : "disabled")}
            ${button("Opciones", "options")}
          </div>
          <div class="status-row">
            <span class="pill">API ${this.runtimeConfig.apiBaseUrl}</span>
            <span class="pill">${this.auth.user ? `Sesión ${this.auth.user.username}` : "Sin sesión online"}</span>
          </div>
        </div>
      </section>
    `;
    this.bindActions({
      quick: () => this.go("quick"),
      story: () => this.go("story"),
      online: () => {
        if (!canOnline) {
          this.toast("Terminá la misión 1 para desbloquear Online.");
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
      <section class="scene card-scene">
        <div class="scene-header">
          <h2>Juego rápido</h2>
          ${button("Volver", "back", "ghost")}
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
        this.go("quick", { ...this.sceneParams, fighterId: event.currentTarget.dataset.value, enemyId: selectedEnemy, arenaId: selectedArena }),
      "pick-enemy": (event) =>
        this.go("quick", { ...this.sceneParams, fighterId: selectedFighter, enemyId: event.currentTarget.dataset.value, arenaId: selectedArena }),
      "pick-arena": (event) =>
        this.go("quick", { ...this.sceneParams, fighterId: selectedFighter, enemyId: selectedEnemy, arenaId: event.currentTarget.dataset.value }),
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
      <section class="scene card-scene">
        <div class="scene-header">
          <h2>Modo historia</h2>
          ${button("Volver", "back", "ghost")}
        </div>
        <div class="story-banner">
          <div>
            <span class="eyebrow">ACTO 1 · EL DESPERTAR</span>
            <h3>Entre los muertos</h3>
            <p>Primer FTUE narrativo en máximo 2 minutos. Kenji despierta, pelea y desbloquea el menú completo.</p>
          </div>
          ${button("Continuar", "continue-story")}
        </div>
        <div class="mission-grid">
          ${this.data.missions
            .map((mission) => {
              const locked = mission.number > unlockedMission;
              return `
                <article class="mission-card ${locked ? "locked" : ""}">
                  <img src="${this.data.arenasById[mission.arena_id].backgroundUrl}" alt="${mission.title}" />
                  <div class="mission-copy">
                    <span class="eyebrow">MISIÓN ${mission.number}</span>
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
    this.stage.querySelectorAll('[data-action="play-mission"]').forEach((buttonNode, index) => {
      if (buttonNode.classList.contains("disabled")) return;
      buttonNode.addEventListener("click", () => this.startStoryMission(this.data.missions[index]));
    });
    this.bindActions({
      back: () => this.go("menu"),
      "continue-story": () => this.startStoryMission(this.data.missions[Math.max(0, unlockedMission - 1)]),
    });
  }

  async renderOnlineMenu() {
    if (!this.auth.token) {
      this.stage.innerHTML = `
        <section class="scene auth-scene">
          <div class="auth-card">
            <h2>Modo online</h2>
            <p>Necesitás una cuenta para crear o unirte a una sala Socket.IO.</p>
            <form id="login-form" class="stack-form">
              <input name="identity" placeholder="Usuario o email" value="${this.onlineProfile.username || ""}" />
              <input name="password" type="password" placeholder="Contraseña" />
              <div class="form-actions">
                ${button("Entrar", "login")}
                ${button("Volver", "back", "ghost")}
              </div>
            </form>
            <div class="divider"></div>
            <form id="register-form" class="stack-form">
              <input name="username" placeholder="Usuario" value="${this.onlineProfile.username || ""}" />
              <input name="email" type="email" placeholder="Email" />
              <input name="password" type="password" placeholder="Contraseña" />
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
      this.bindActions({ back: () => this.go("menu") });
      return;
    }

    try {
      const [rooms, ranking] = await Promise.all([this.api.rooms(), this.api.ranking()]);
      this.onlineLists = { rooms, ranking };
    } catch (_error) {
      this.onlineLists = { rooms: [], ranking: [] };
    }

    const clans = this.data.clans;
    const weapons = this.data.onlineWeapons;
    this.stage.innerHTML = `
      <section class="scene online-scene">
        <div class="scene-header">
          <h2>Online</h2>
          <div class="inline-actions">
            ${button("Cerrar sesión", "logout", "ghost")}
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
            <label>Código sala</label>
            <input id="room-code" placeholder="ABCD12" />
            <div class="form-actions">
              ${button("Crear sala", "create-room")}
              ${button("Unirme", "join-room")}
            </div>
          </div>
          <div class="card">
            <h3>Salas</h3>
            <div class="list-panel">
              ${this.onlineLists.rooms.length ? this.onlineLists.rooms.map((room) => `<div class="list-row">${room.roomCode} · ${room.status}</div>`).join("") : "<div class='list-row'>No hay salas públicas visibles.</div>"}
            </div>
            <h3>Ranking</h3>
            <div class="list-panel">
              ${this.onlineLists.ranking.length ? this.onlineLists.ranking.map((row) => `<div class="list-row">${row.username} · ${row.points} pts</div>`).join("") : "<div class='list-row'>Sin ranking disponible.</div>"}
            </div>
          </div>
        </div>
      </section>
    `;
    this.bindActions({
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
      <section class="scene auth-scene">
        <div class="auth-card">
          <h2>Sala ${snapshot.roomCode}</h2>
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
        this.go("online");
      },
    });
  }

  renderOptions() {
    this.stage.innerHTML = `
      <section class="scene card-scene">
        <div class="scene-header">
          <h2>Opciones</h2>
          ${button("Volver", "back", "ghost")}
        </div>
        <div class="online-grid">
          <div class="card">
            <h3>Conexión</h3>
            <label>API base URL</label>
            <input id="api-url" value="${this.settings.apiBaseUrl}" placeholder="https://api.tudominio.com" />
            <label>Socket URL</label>
            <input id="socket-url" value="${this.settings.socketUrl}" placeholder="https://api.tudominio.com" />
            <div class="form-actions">
              ${button("Guardar", "save-options")}
              ${button("Pantalla completa", "fullscreen")}
            </div>
            <p class="helper">En producción, no uses localhost. Si dejás vacío, el cliente intenta usar el mismo origen.</p>
          </div>
          <div class="card">
            <h3>Controles</h3>
            <div class="list-panel">
              <div class="list-row">Mover: A / D o botones ◀ ▶</div>
              <div class="list-row">Saltar: W o ▲</div>
              <div class="list-row">Agacharse: S o ▼</div>
              <div class="list-row">Atacar: J o ATK</div>
              <div class="list-row">Bloquear: I o BLK</div>
              <div class="list-row">Dash / Esquivar: L o DASH</div>
              <div class="list-row">Especial: K o SP</div>
              <div class="list-row">Pausa: ESC o botón II</div>
            </div>
          </div>
        </div>
      </section>
    `;
    this.bindActions({
      back: () => this.go("menu"),
      "save-options": () => {
        this.settings.apiBaseUrl = this.stage.querySelector("#api-url").value.trim();
        this.settings.socketUrl = this.stage.querySelector("#socket-url").value.trim();
        saveSettings(this.settings);
        this.runtimeConfig = resolveRuntimeConfig(this.settings);
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
          this.toast("La pantalla completa depende del navegador o WebView.");
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
        storyHints: mission.number === 1
          ? [
              { text: "Movete con A/D o los botones laterales", duration: 2400, gap: 900 },
              { text: "Atacá con J o ATK", duration: 2200, gap: 900 },
              { text: "Bloqueá con I o BLK, y usá L o DASH para esquivar", duration: 2600, gap: 900 },
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
          maxHealth: localMeta.maxHealth,
          maxStamina: localMeta.maxStamina,
          attackPower: localMeta.attackPower,
        },
        enemy: {
          ...enemyMeta,
          id: enemyMeta.clanId,
          name: enemyMeta.username,
          portrait: this.data.assetUrl(enemyMeta.portrait),
          maxHealth: enemyMeta.maxHealth,
          maxStamina: enemyMeta.maxStamina,
          attackPower: enemyMeta.attackPower,
        },
        playerWeapon,
        enemyWeapon,
        realtime: this.realtime,
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
      this.toast("Kenji cayó. Reintentá la misión.");
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
    const panels = [...(cutscene.panels || [])];
    let index = 0;
    const renderPanel = () => {
      const panel = panels[index];
      if (!panel) {
        onComplete();
        return;
      }
      this.stage.innerHTML = `
        <section class="scene cutscene-scene">
          <img class="cutscene-image" src="${this.data.assetUrl(panel.image)}" alt="${panel.speaker}" />
          <div class="cutscene-panel">
            <span class="eyebrow">${panel.speaker}</span>
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
      this.toast("Ingresá un código de sala.");
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
