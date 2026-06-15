const LOGICAL_WIDTH = 1280;
const LOGICAL_HEIGHT = 720;
const GROUND_Y = 560;
const SPRITE_FRAME_COUNT = 7;
const TOUCH_BUTTONS = [
  { action: "left", label: "IZQ", group: "move" },
  { action: "right", label: "DER", group: "move" },
  { action: "up", label: "SALTO", group: "move jump" },
  { action: "down", label: "ABAJO", group: "move" },
  { action: "attack", label: "GOLPE", group: "act primary" },
  { action: "block", label: "BLOQ", group: "act" },
  { action: "dash", label: "DASH", group: "act" },
  { action: "special", label: "ESPECIAL", group: "act primary" },
];

const KEY_MAP = {
  KeyA: "left",
  KeyD: "right",
  KeyW: "up",
  KeyS: "down",
  KeyJ: "attack",
  KeyI: "block",
  KeyL: "dash",
  KeyK: "special",
};

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function lerp(start, end, amount) {
  return start + (end - start) * amount;
}

function distance(a, b) {
  return Math.abs(a.x - b.x);
}

function createImage(src) {
  const image = new Image();
  image.src = src;
  return image;
}

function buildSpriteFrameRects(image) {
  const frameWidth = Math.floor(image.naturalWidth / SPRITE_FRAME_COUNT);
  const frameHeight = image.naturalHeight;
  const canvas = document.createElement("canvas");
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(image, 0, 0);
  const rects = [];

  for (let index = 0; index < SPRITE_FRAME_COUNT; index += 1) {
    const startX = index * frameWidth;
    const data = ctx.getImageData(startX, 0, frameWidth, frameHeight).data;
    let minX = frameWidth;
    let minY = frameHeight;
    let maxX = -1;
    let maxY = -1;
    for (let y = 0; y < frameHeight; y += 1) {
      for (let x = 0; x < frameWidth; x += 1) {
        const alpha = data[(y * frameWidth + x) * 4 + 3];
        if (alpha < 10) continue;
        if (x < minX) minX = x;
        if (y < minY) minY = y;
        if (x > maxX) maxX = x;
        if (y > maxY) maxY = y;
      }
    }
    if (maxX === -1) {
      rects.push({ sx: startX, sy: 0, sw: frameWidth, sh: frameHeight });
      continue;
    }
    rects.push({
      sx: startX + minX,
      sy: minY,
      sw: Math.max(1, maxX - minX + 1),
      sh: Math.max(1, maxY - minY + 1),
    });
  }

  return rects;
}

function fighterColor(source, fallback) {
  if (Array.isArray(source?.color)) return source.color;
  return fallback;
}

function calcWeaponConfig(weapon) {
  return {
    lightDamage: weapon?.damage_light || 12,
    specialDamage: weapon?.damage_heavy || 24,
    range: weapon?.range || 74,
    cooldown: weapon?.cooldown || 0.3,
    staminaCost: weapon?.stamina_cost || 12,
  };
}

function makeFighter(meta, side, accent, weapon, socketId = null) {
  const spriteUrl = meta.spriteUrl || meta.sprite_sheet || meta.spriteSheet || "";
  return {
    socketId,
    id: meta.id || side,
    name: meta.name || meta.fighterName || "Guerrero",
    portraitUrl: meta.portraitUrl || meta.portrait || "",
    portraitImage: createImage(meta.portraitUrl || meta.portrait || ""),
    spriteUrl,
    spriteSheetImage: createImage(spriteUrl),
    spriteFrameRects: null,
    accent,
    x: side === "left" ? 220 : 1060,
    y: GROUND_Y,
    vx: 0,
    vy: 0,
    width: 88,
    height: 164,
    facing: side === "left" ? 1 : -1,
    health: meta.max_health || meta.maxHealth || 100,
    maxHealth: meta.max_health || meta.maxHealth || 100,
    stamina: meta.max_stamina || meta.maxStamina || 100,
    maxStamina: meta.max_stamina || meta.maxStamina || 100,
    speed: meta.speed || 210,
    attackPower: meta.attack_power || meta.attackPower || 18,
    defense: meta.defense || 8,
    roundWins: meta.roundWins || 0,
    weapon: calcWeaponConfig(weapon),
    onGround: true,
    isBlocking: false,
    crouching: false,
    dodgeTimer: 0,
    hitFlash: 0,
    attackCooldown: 0,
    specialCooldown: 0,
    action: null,
    remoteState: null,
    bobTime: Math.random() * Math.PI * 2,
  };
}

export class BattleView {
  constructor(options) {
    this.options = options;
    this.mode = options.mode;
    this.container = options.container;
    this.realtime = options.realtime || null;
    this.audio = options.audio || null;
    this.localInput = {
      left: false,
      right: false,
      up: false,
      down: false,
      block: false,
    };
    this.lastSentInput = 0;
    this.paused = false;
    this.active = false;
    this.pendingTimers = new Set();
    this.cleanupFns = [];
    this.overlayText = "";
    this.overlaySubtext = "";
    this.round = options.currentRound || 1;
    this.matchEnded = false;
    this.roundIntro = { timer: 1.0, sequence: ["3", "2", "1", "FIGHT"], index: -1 };
    this.storyHints = options.storyHints || [];
    this.activeHint = "";
    this.background = createImage(options.arena.backgroundUrl);
    this.floor = createImage(options.arena.floorUrl);
    this.player = makeFighter(
      options.player,
      "left",
      fighterColor(options.player, [190, 62, 72]),
      options.playerWeapon,
      options.player.socketId || options.onlineSocketId || null,
    );
    this.enemy = makeFighter(
      options.enemy,
      "right",
      fighterColor(options.enemy, [86, 122, 212]),
      options.enemyWeapon,
      options.enemy.socketId || null,
    );
    this.lastFrame = 0;
  }

  mount() {
    this.container.innerHTML = `
      <section class="battle-screen">
        <canvas class="battle-canvas" width="${LOGICAL_WIDTH}" height="${LOGICAL_HEIGHT}"></canvas>
        <button class="battle-pause-btn" type="button">II</button>
        <div class="battle-status">
          <span class="battle-chip">${this.mode === "online" ? "ONLINE" : this.mode === "story" ? "HISTORIA" : "JUEGO RAPIDO"}</span>
          <span class="battle-chip">RONDAS ${this.player.roundWins}-${this.enemy.roundWins}</span>
          <span class="battle-chip">CONTROLES LISTOS</span>
        </div>
        <div class="battle-controls">
          <div class="touch-pad move-pad" data-title="MOVIMIENTO"></div>
          <div class="touch-pad action-pad" data-title="COMBATE"></div>
        </div>
        <div class="battle-modal hidden"></div>
      </section>
    `;
    this.canvas = this.container.querySelector(".battle-canvas");
    this.ctx = this.canvas.getContext("2d");
    this.controlsNode = this.container.querySelector(".battle-controls");
    this.modalNode = this.container.querySelector(".battle-modal");
    this.container.querySelector(".battle-pause-btn").addEventListener("click", () => this.togglePause());
    this.renderTouchControls();
    this.bindInput();
    this.bindOnline();
    this.startRoundIntro(this.round);
    this.active = true;
    this.scheduleHint();
    this.frameHandle = requestAnimationFrame((timestamp) => this.loop(timestamp));
  }

  destroy() {
    this.active = false;
    cancelAnimationFrame(this.frameHandle);
    this.cleanupFns.forEach((cleanup) => cleanup());
    this.pendingTimers.forEach((timer) => clearTimeout(timer));
    this.pendingTimers.clear();
    this.container.innerHTML = "";
  }

  bindOnline() {
    if (this.mode !== "online" || !this.realtime) return;
    this.cleanupFns.push(
      this.realtime.on("opponent_input", (payload) => {
        this.enemy.remoteState = payload;
        this.enemy.isBlocking = Boolean(payload.block);
        this.enemy.crouching = Boolean(payload.down);
      }),
      this.realtime.on("opponent_attack", (payload) => {
        this.startAction(this.enemy, payload.attackType === "special" ? "special" : "attack", false);
      }),
      this.realtime.on("opponent_block", (payload) => {
        this.enemy.isBlocking = Boolean(payload.active);
      }),
      this.realtime.on("opponent_dodge", () => {
        this.triggerDash(this.enemy);
      }),
      this.realtime.on("fighter_hit", (payload) => {
        const defender =
          payload.defenderSocketId === this.player.socketId
            ? this.player
            : payload.defenderSocketId === this.enemy.socketId
              ? this.enemy
              : null;
        if (!defender) return;
        defender.health = clamp(payload.defenderHealth ?? defender.health, 0, defender.maxHealth);
        defender.hitFlash = 0.18;
      }),
      this.realtime.on("health_update", (payload) => {
        payload.players?.forEach((meta) => {
          const fighter =
            meta.socketId === this.player.socketId ? this.player : meta.socketId === this.enemy.socketId ? this.enemy : null;
          if (!fighter) return;
          fighter.health = clamp(meta.health ?? fighter.health, 0, fighter.maxHealth);
          fighter.roundWins = meta.roundWins || 0;
        });
      }),
      this.realtime.on("round_finished", (payload) => {
        this.player.roundWins = payload.players?.find((item) => item.socketId === this.player.socketId)?.roundWins || this.player.roundWins;
        this.enemy.roundWins = payload.players?.find((item) => item.socketId === this.enemy.socketId)?.roundWins || this.enemy.roundWins;
        this.overlayText = payload.winnerSocketId === this.player.socketId ? "ROUND GANADO" : "ROUND PERDIDO";
        this.overlaySubtext = `Marcador ${this.player.roundWins} - ${this.enemy.roundWins}`;
      }),
      this.realtime.on("round_started", (payload) => {
        this.round = payload.currentRound || this.round + 1;
        this.syncPlayers(payload.players || [], true);
        this.resetPositions();
        this.startRoundIntro(this.round);
      }),
      this.realtime.on("match_finished", (payload) => {
        this.matchEnded = true;
        this.overlayText = payload.winnerSocketId === this.player.socketId ? "VICTORIA" : "DERROTA";
        this.overlaySubtext = payload.winnerSocketId === this.player.socketId ? "La sala queda a tu favor." : "El rival se llevo la arena.";
        this.showEndModal(payload.winnerSocketId === this.player.socketId);
      }),
      this.realtime.on("opponent_left", () => {
        this.matchEnded = true;
        this.overlayText = "RIVAL DESCONECTADO";
        this.overlaySubtext = "Se cierra la pelea online.";
        this.showEndModal(true);
      }),
    );
  }

  syncPlayers(players, forceStaminaReset = false) {
    players.forEach((meta) => {
      const fighter =
        meta.socketId === this.player.socketId ? this.player : meta.socketId === this.enemy.socketId ? this.enemy : null;
      if (!fighter) return;
      fighter.health = meta.health ?? fighter.health;
      if (forceStaminaReset) {
        fighter.stamina = meta.stamina ?? fighter.maxStamina;
      }
      fighter.roundWins = meta.roundWins || 0;
    });
  }

  bindInput() {
    const handleKeyDown = (event) => this.handleKeyEvent(event, true);
    const handleKeyUp = (event) => this.handleKeyEvent(event, false);
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    this.cleanupFns.push(() => window.removeEventListener("keydown", handleKeyDown));
    this.cleanupFns.push(() => window.removeEventListener("keyup", handleKeyUp));
  }

  handleKeyEvent(event, pressed) {
    if (event.code === "Escape" && pressed) {
      this.togglePause();
      return;
    }
    const action = KEY_MAP[event.code];
    if (!action) return;
    event.preventDefault();
    if (action === "attack" || action === "dash" || action === "special") {
      if (pressed) this.handleActionPress(action);
      return;
    }
    if (action === "block") {
      this.localInput.block = pressed;
      if (this.mode === "online" && this.realtime) {
        this.realtime.sendBlock({ active: pressed });
      }
      return;
    }
    this.localInput[action] = pressed;
  }

  renderTouchControls() {
    const movePad = this.controlsNode.querySelector(".move-pad");
    const actionPad = this.controlsNode.querySelector(".action-pad");
    TOUCH_BUTTONS.forEach((button) => {
      const element = document.createElement("button");
      element.type = "button";
      element.className = `touch-btn ${button.group}`;
      element.textContent = button.label;
      const press = (pressed) => {
        if (button.action === "attack" || button.action === "dash" || button.action === "special") {
          if (pressed) this.handleActionPress(button.action);
          return;
        }
        if (button.action === "block") {
          this.localInput.block = pressed;
          if (this.mode === "online" && this.realtime) {
            this.realtime.sendBlock({ active: pressed });
          }
          return;
        }
        this.localInput[button.action] = pressed;
      };
      ["pointerdown", "pointerup", "pointercancel", "pointerleave"].forEach((eventName) => {
        element.addEventListener(eventName, (event) => {
          event.preventDefault();
          press(eventName === "pointerdown");
        });
      });
      (button.group.includes("move") ? movePad : actionPad).appendChild(element);
    });
  }

  handleActionPress(action) {
    if (action === "dash") {
      this.triggerDash(this.player);
      if (this.mode === "online" && this.realtime) {
        this.realtime.sendDodge({ at: performance.now() });
      }
      return;
    }
    this.startAction(this.player, action === "special" ? "special" : "attack", true);
  }

  triggerDash(fighter) {
    if (fighter.dodgeTimer > 0 || fighter.stamina < 12 || this.roundIntro.timer > 0 || this.matchEnded) return;
    fighter.dodgeTimer = 0.22;
    fighter.stamina = clamp(fighter.stamina - 12, 0, fighter.maxStamina);
    const dir = fighter.facing || 1;
    fighter.vx = dir * 720;
  }

  startAction(fighter, type, shouldBroadcast) {
    const target = fighter === this.player ? this.enemy : this.player;
    const cooldownKey = type === "special" ? "specialCooldown" : "attackCooldown";
    if (fighter[cooldownKey] > 0 || this.roundIntro.timer > 0 || this.matchEnded) return;
    const cost = type === "special" ? fighter.weapon.staminaCost + 10 : fighter.weapon.staminaCost;
    if (fighter.stamina < cost) return;
    fighter.stamina = clamp(fighter.stamina - cost, 0, fighter.maxStamina);
    fighter[cooldownKey] = type === "special" ? fighter.weapon.cooldown + 0.45 : fighter.weapon.cooldown;
    fighter.action = {
      type,
      timer: 0,
      duration: type === "special" ? 0.44 : 0.26,
      hitDone: false,
    };
    if (this.mode === "online" && fighter === this.player && shouldBroadcast && this.realtime) {
      this.realtime.sendAttack({ attackType: type });
    }
    if (this.mode !== "online" || fighter !== this.enemy) {
      this.tryResolveHit(fighter, target, type);
    }
  }

  tryResolveHit(attacker, defender, attackType) {
    const range = attacker.weapon.range + (attackType === "special" ? 26 : 0);
    if (distance(attacker, defender) > range) return;
    if (defender.dodgeTimer > 0.04) return;
    const baseDamage =
      (attackType === "special" ? attacker.weapon.specialDamage : attacker.weapon.lightDamage) +
      attacker.attackPower * (attackType === "special" ? 0.45 : 0.25);
    const blocked = defender.isBlocking;
    const reduced = blocked ? baseDamage * 0.38 : baseDamage;
    const damage = Math.max(1, Math.round(reduced - defender.defense * 0.28));
    if (this.mode === "online" && attacker === this.player && this.realtime) {
      this.realtime.sendHit({
        attackType: attackType === "special" ? "attack_heavy" : "attack_light",
        damage,
        blocked,
        knockback: blocked ? 8 : attackType === "special" ? 28 : 18,
      });
      return;
    }
    defender.health = clamp(defender.health - damage, 0, defender.maxHealth);
    defender.hitFlash = 0.18;
    this.audio?.playEffect(
      attackType === "special" ? "hitHeavy" : attackType === "attack" ? "hitLight" : "hitKick",
    );
    defender.vx += (attacker === this.player ? 1 : -1) * (blocked ? 90 : attackType === "special" ? 180 : 110);
    if (defender.health <= 0) {
      this.finishRound(attacker === this.player);
    }
  }

  finishRound(playerWon) {
    const winner = playerWon ? this.player : this.enemy;
    winner.roundWins += 1;
    this.overlayText = playerWon ? "ROUND GANADO" : "ROUND PERDIDO";
    this.overlaySubtext = `Marcador ${this.player.roundWins} - ${this.enemy.roundWins}`;
    if (winner.roundWins >= 2) {
      this.matchEnded = true;
      this.showEndModal(playerWon);
      return;
    }
    const timer = setTimeout(() => {
      this.round += 1;
      this.resetFighters();
      this.startRoundIntro(this.round);
      this.pendingTimers.delete(timer);
    }, 1500);
    this.pendingTimers.add(timer);
  }

  showEndModal(playerWon) {
    this.modalNode.classList.remove("hidden");
    this.modalNode.innerHTML = `
      <div class="battle-modal-card">
        <h2>${playerWon ? "Victoria" : "Derrota"}</h2>
        <p>${playerWon ? "La arena queda a tu favor." : "Toma aire y vuelve a intentarlo."}</p>
        <div class="battle-modal-actions">
          <button type="button" data-action="menu">Volver</button>
          ${this.mode !== "online" ? '<button type="button" data-action="retry">Revancha</button>' : ""}
        </div>
      </div>
    `;
    this.modalNode.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        const action = button.dataset.action;
        if (action === "retry") {
          this.options.onRetry?.();
          return;
        }
        this.options.onExit?.(playerWon);
      });
    });
    this.options.onMatchEnd?.(playerWon);
  }

  resetFighters() {
    [this.player, this.enemy].forEach((fighter) => {
      fighter.health = fighter.maxHealth;
      fighter.stamina = fighter.maxStamina;
      fighter.vx = 0;
      fighter.vy = 0;
      fighter.action = null;
      fighter.dodgeTimer = 0;
      fighter.isBlocking = false;
    });
    this.resetPositions();
  }

  resetPositions() {
    this.player.x = 220;
    this.enemy.x = 1060;
    this.player.y = GROUND_Y;
    this.enemy.y = GROUND_Y;
    this.player.facing = 1;
    this.enemy.facing = -1;
  }

  scheduleHint() {
    if (!this.storyHints.length) return;
    const showNext = (index = 0) => {
      const hint = this.storyHints[index];
      if (!hint) return;
      this.activeHint = hint.text;
      const timer = setTimeout(() => {
        this.activeHint = "";
        this.pendingTimers.delete(timer);
        if (index + 1 < this.storyHints.length) {
          const nextTimer = setTimeout(() => {
            this.pendingTimers.delete(nextTimer);
            showNext(index + 1);
          }, hint.gap ?? 1200);
          this.pendingTimers.add(nextTimer);
        }
      }, hint.duration ?? 2600);
      this.pendingTimers.add(timer);
    };
    showNext(0);
  }

  togglePause() {
    if (this.matchEnded) return;
    this.paused = !this.paused;
    this.overlayText = this.paused ? "PAUSA" : "";
    this.overlaySubtext = this.paused ? "Toca II para continuar" : "";
  }

  startRoundIntro(round) {
    this.overlayText = `ROUND ${round}`;
    this.overlaySubtext = "Preparado";
    this.roundIntro = {
      timer: 1.0,
      sequence: ["3", "2", "1", "FIGHT"],
      index: -1,
    };
  }

  updateRoundIntro(dt) {
    if (this.roundIntro.timer <= 0) return;
    this.roundIntro.timer -= dt;
    if (this.roundIntro.timer > 0) return;
    this.roundIntro.index += 1;
    if (this.roundIntro.index >= this.roundIntro.sequence.length) {
      this.roundIntro.timer = 0;
      this.overlayText = "";
      this.overlaySubtext = "";
      return;
    }
    this.overlayText = this.roundIntro.sequence[this.roundIntro.index];
    this.overlaySubtext = this.roundIntro.index < 3 ? "Dos victorias cierran la pelea" : "Lucha";
    if (this.roundIntro.index < 3) {
      this.audio?.playEffect("countTick");
    } else {
      this.audio?.playEffect("fightStart");
    }
    this.roundIntro.timer = this.roundIntro.index < 3 ? 0.8 : 0.95;
  }

  loop(timestamp) {
    if (!this.active) return;
    const dt = Math.min(0.033, (timestamp - (this.lastFrame || timestamp)) / 1000);
    this.lastFrame = timestamp;
    if (!this.paused) {
      this.update(dt);
    }
    this.render();
    this.frameHandle = requestAnimationFrame((next) => this.loop(next));
  }

  update(dt) {
    this.updateRoundIntro(dt);
    if (this.roundIntro.timer > 0) return;
    this.updateFighter(this.player, this.enemy, dt, this.localInput, true);
    if (this.mode === "online") {
      this.updateRemoteFighter(dt);
      this.sendOnlineInput(dt);
    } else {
      const aiInput = this.computeAiInput(dt);
      this.updateFighter(this.enemy, this.player, dt, aiInput, false);
    }
    this.resolveSpacing();
  }

  sendOnlineInput(dt) {
    this.lastSentInput += dt;
    if (this.lastSentInput < 1 / 15 || !this.realtime) return;
    this.lastSentInput = 0;
    this.realtime.sendInput({
      x: this.player.x,
      y: this.player.y,
      vx: this.player.vx,
      vy: this.player.vy,
      facing: this.player.facing,
      block: this.player.isBlocking,
      down: this.player.crouching,
      state: this.player.action?.type || (this.player.dodgeTimer > 0 ? "dash" : "idle"),
    });
  }

  updateRemoteFighter(dt) {
    const state = this.enemy.remoteState;
    if (!state) return;
    this.enemy.x = lerp(this.enemy.x, state.x ?? this.enemy.x, clamp(dt * 10, 0, 1));
    this.enemy.y = lerp(this.enemy.y, state.y ?? this.enemy.y, clamp(dt * 10, 0, 1));
    this.enemy.facing = state.facing ?? this.enemy.facing;
    this.enemy.isBlocking = Boolean(state.block);
    this.enemy.crouching = Boolean(state.down);
  }

  updateFighter(fighter, target, dt, input, allowActions) {
    fighter.bobTime += dt * 4;
    fighter.attackCooldown = Math.max(0, fighter.attackCooldown - dt);
    fighter.specialCooldown = Math.max(0, fighter.specialCooldown - dt);
    fighter.dodgeTimer = Math.max(0, fighter.dodgeTimer - dt);
    fighter.hitFlash = Math.max(0, fighter.hitFlash - dt);
    fighter.isBlocking = Boolean(input.block);
    fighter.crouching = Boolean(input.down);

    if (this.mode !== "online") {
      fighter.health = clamp(fighter.health + fighter.maxHealth * 0.01 * dt, 0, fighter.maxHealth);
    }
    fighter.stamina = clamp(fighter.stamina + fighter.maxStamina * 0.08 * dt, 0, fighter.maxStamina);

    if (fighter.action) {
      fighter.action.timer += dt;
      if (!fighter.action.hitDone && fighter.action.timer >= (fighter.action.type === "special" ? 0.18 : 0.12)) {
        fighter.action.hitDone = true;
        if (allowActions) {
          this.tryResolveHit(fighter, target, fighter.action.type);
        }
      }
      if (fighter.action.timer >= fighter.action.duration) {
        fighter.action = null;
      }
    }

    const speedFactor = fighter.crouching ? 0.46 : fighter.isBlocking ? 0.52 : fighter.dodgeTimer > 0 ? 1.4 : 1;
    const moveDir = (input.left ? -1 : 0) + (input.right ? 1 : 0);
    fighter.vx = moveDir * fighter.speed * speedFactor;
    if (moveDir !== 0) fighter.facing = moveDir;
    if (input.up && fighter.onGround) {
      fighter.vy = -520;
      fighter.onGround = false;
    }
    fighter.vy += 1200 * dt;
    fighter.x = clamp(fighter.x + fighter.vx * dt, 60, LOGICAL_WIDTH - 60);
    fighter.y += fighter.vy * dt;
    if (fighter.y >= GROUND_Y) {
      fighter.y = GROUND_Y;
      fighter.vy = 0;
      fighter.onGround = true;
    }
  }

  computeAiInput(dt) {
    if (!this.aiState) {
      this.aiState = { timer: 0, command: {} };
    }
    this.aiState.timer -= dt;
    if (this.aiState.timer <= 0) {
      const gap = distance(this.enemy, this.player);
      const wantsAttack = gap < this.enemy.weapon.range + 18;
      const direction = this.player.x < this.enemy.x ? -1 : 1;
      this.aiState.command = {
        left: !wantsAttack && direction < 0,
        right: !wantsAttack && direction > 0,
        up: Math.random() < 0.1,
        down: gap < 110 && Math.random() < 0.2,
        block: gap < 130 && Math.random() < 0.18,
      };
      this.aiState.timer = 0.18 + Math.random() * 0.36;
      if (wantsAttack) {
        const special = Math.random() < 0.3;
        this.startAction(this.enemy, special ? "special" : "attack", false);
      } else if (gap > 180 && Math.random() < 0.12) {
        this.triggerDash(this.enemy);
      }
    }
    return this.aiState.command;
  }

  resolveSpacing() {
    const overlap = (this.player.width + this.enemy.width) * 0.5 - distance(this.player, this.enemy);
    if (overlap > 0) {
      this.player.x -= overlap * 0.5;
      this.enemy.x += overlap * 0.5;
      if (this.player.x > this.enemy.x) {
        const middle = (this.player.x + this.enemy.x) / 2;
        this.player.x = middle - 44;
        this.enemy.x = middle + 44;
      }
      this.player.x = clamp(this.player.x, 60, LOGICAL_WIDTH - 60);
      this.enemy.x = clamp(this.enemy.x, 60, LOGICAL_WIDTH - 60);
    }
    this.player.facing = this.player.x <= this.enemy.x ? 1 : -1;
    this.enemy.facing = this.enemy.x >= this.player.x ? -1 : 1;
  }

  render() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT);
    if (this.background.complete && this.background.naturalWidth > 0) {
      ctx.drawImage(this.background, 0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT);
    } else {
      const gradient = ctx.createLinearGradient(0, 0, 0, LOGICAL_HEIGHT);
      gradient.addColorStop(0, "#241b1e");
      gradient.addColorStop(1, "#08090c");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT);
    }
    ctx.fillStyle = "rgba(6,8,14,0.24)";
    ctx.fillRect(0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT);
    if (this.floor.complete && this.floor.naturalWidth > 0) {
      ctx.drawImage(this.floor, 0, GROUND_Y - 20, LOGICAL_WIDTH, LOGICAL_HEIGHT - (GROUND_Y - 20));
    } else {
      ctx.fillStyle = "#2a272c";
      ctx.fillRect(0, GROUND_Y, LOGICAL_WIDTH, 160);
      ctx.fillStyle = "#816447";
      ctx.fillRect(0, GROUND_Y, LOGICAL_WIDTH, 8);
    }
    this.drawFighter(this.enemy);
    this.drawFighter(this.player);
    this.drawHud();
    this.drawOverlayText();
    if (this.activeHint) {
      ctx.fillStyle = "rgba(0,0,0,0.72)";
      ctx.fillRect(250, 116, 780, 58);
      ctx.strokeStyle = "rgba(214,178,96,0.95)";
      ctx.strokeRect(250, 116, 780, 58);
      ctx.fillStyle = "#f4f0e1";
      ctx.font = "600 24px Arial";
      ctx.textAlign = "center";
      ctx.fillText(this.activeHint, LOGICAL_WIDTH / 2, 152);
    }
  }

  resolveSpriteFrameIndex(fighter) {
    if (fighter.hitFlash > 0.08 && !fighter.action) return 6;
    if (fighter.action?.type === "special") return 2;
    if (fighter.action?.type === "attack") return 1;
    if (!fighter.onGround || fighter.dodgeTimer > 0) return 4;
    if (fighter.crouching || fighter.isBlocking) return 5;
    return 0;
  }

  drawSpriteFighter(fighter) {
    const image = fighter.spriteSheetImage;
    if (!image?.complete || image.naturalWidth <= 0 || image.naturalHeight <= 0) return false;
    if (!fighter.spriteFrameRects) {
      fighter.spriteFrameRects = buildSpriteFrameRects(image);
    }
    const frame = fighter.spriteFrameRects[this.resolveSpriteFrameIndex(fighter)];
    if (!frame) return false;

    const ctx = this.ctx;
    const bob = Math.sin(fighter.bobTime * 1.35) * 2.2;
    const poseOffsetX =
      fighter.action?.type === "special"
        ? 14
        : fighter.action?.type === "attack"
          ? 10
          : !fighter.onGround || fighter.dodgeTimer > 0
            ? 12
            : fighter.crouching || fighter.isBlocking
              ? 8
              : 0;
    const targetHeight = fighter.crouching || fighter.isBlocking ? 164 : !fighter.onGround ? 176 : 184;
    const scale = targetHeight / frame.sh;
    const drawWidth = frame.sw * scale;
    const drawHeight = frame.sh * scale;
    const drawX = -drawWidth / 2;
    const drawY = -drawHeight + (fighter.crouching || fighter.isBlocking ? 26 : 10);

    ctx.save();
    ctx.translate(fighter.x + poseOffsetX * fighter.facing, fighter.y + bob);
    if (fighter.facing < 0) ctx.scale(-1, 1);
    ctx.fillStyle = fighter.hitFlash > 0 ? "rgba(255,240,240,0.95)" : "rgba(0,0,0,0.26)";
    ctx.beginPath();
    ctx.ellipse(0, 12, fighter.crouching ? 52 : 46, fighter.onGround ? 16 : 11, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.drawImage(image, frame.sx, frame.sy, frame.sw, frame.sh, drawX, drawY, drawWidth, drawHeight);
    if (fighter.isBlocking) {
      ctx.strokeStyle = "rgba(198,228,255,0.92)";
      ctx.lineWidth = 8;
      ctx.beginPath();
      ctx.arc(8, -72, 30, -0.5, 1.4);
      ctx.stroke();
    }
    if (fighter.hitFlash > 0) {
      ctx.strokeStyle = "rgba(255,255,255,0.78)";
      ctx.lineWidth = 3;
      ctx.strokeRect(drawX - 4, drawY - 4, drawWidth + 8, drawHeight + 8);
    }
    ctx.restore();
    return true;
  }

  drawFighter(fighter) {
    if (this.drawSpriteFighter(fighter)) {
      return;
    }
    const ctx = this.ctx;
    const bob = Math.sin(fighter.bobTime * 1.4) * 2.8;
    const x = fighter.x;
    const y = fighter.y + bob;
    const attacking = fighter.action?.type === "attack";
    const special = fighter.action?.type === "special";
    const crouching = fighter.crouching;
    const blocking = fighter.isBlocking;
    const airborne = !fighter.onGround;
    const dashing = fighter.dodgeTimer > 0;
    const stanceOffset = crouching ? 24 : airborne ? -18 : 0;
    const torsoTilt = special ? 0.28 : attacking ? 0.12 : blocking ? -0.08 : 0;
    const armReach = special ? 82 : attacking ? 58 : blocking ? 20 : 28;
    const bladeReach = special ? 126 : attacking ? 92 : 54;
    const robeDark = fighter.accent.map((value) => Math.max(24, Math.round(value * 0.42)));
    const robeLight = fighter.accent.map((value) => Math.min(255, Math.round(value * 1.08)));
    ctx.save();
    ctx.translate(x, y);
    if (fighter.facing < 0) ctx.scale(-1, 1);

    ctx.fillStyle = fighter.hitFlash > 0 ? "rgba(255,240,240,0.95)" : "rgba(0,0,0,0.26)";
    ctx.beginPath();
    ctx.ellipse(0, 12, crouching ? 52 : 46, fighter.onGround ? 16 : 11, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.translate(0, special ? -16 : dashing ? -8 : 0);
    ctx.translate(0, stanceOffset);
    ctx.rotate(torsoTilt);

    ctx.fillStyle = `rgb(${robeDark.join(",")})`;
    ctx.beginPath();
    ctx.moveTo(-20, -108);
    ctx.lineTo(18, -108);
    ctx.lineTo(26, -38);
    ctx.lineTo(-28, -38);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = `rgb(${robeLight.join(",")})`;
    ctx.beginPath();
    ctx.moveTo(-24, -110);
    ctx.lineTo(22, -110);
    ctx.lineTo(26, -46);
    ctx.lineTo(0, crouching ? -8 : 6);
    ctx.lineTo(-28, -46);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = "#d7b15d";
    ctx.fillRect(-22, -76, 44, 8);
    ctx.fillStyle = "#1b1714";
    ctx.fillRect(-18, -68, 36, 12);

    ctx.fillStyle = "#f0d3b0";
    ctx.beginPath();
    ctx.arc(0, -132, 23, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#16171d";
    ctx.beginPath();
    ctx.arc(0, -143, 15, Math.PI, 0);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(10, -152, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#b63c3c";
    ctx.fillRect(-18, -138, 36, 6);

    ctx.strokeStyle = "#17181d";
    ctx.lineWidth = 12;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(-10, -34);
    ctx.lineTo(crouching ? -14 : -18, 24);
    ctx.moveTo(12, -34);
    ctx.lineTo(crouching ? 18 : 16, 24);
    ctx.stroke();

    ctx.strokeStyle = "#0e0f14";
    ctx.lineWidth = 14;
    ctx.beginPath();
    ctx.moveTo(-8, -92);
    ctx.lineTo(-34, blocking ? -58 : -64);
    ctx.stroke();

    ctx.strokeStyle = "#f0d3b0";
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.moveTo(10, -92);
    ctx.lineTo(18 + armReach, blocking ? -82 : special ? -104 : -90);
    ctx.stroke();

    ctx.strokeStyle = special ? "#f4ece0" : "#cfd6e2";
    ctx.lineWidth = special ? 7 : 5;
    ctx.beginPath();
    ctx.moveTo(26, -90);
    ctx.lineTo(24 + bladeReach, special ? -130 : -102);
    ctx.stroke();

    ctx.strokeStyle = "#6b717c";
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(18, -88);
    ctx.lineTo(36, -78);
    ctx.stroke();

    if (blocking) {
      ctx.strokeStyle = "rgba(198,228,255,0.92)";
      ctx.lineWidth = 8;
      ctx.beginPath();
      ctx.arc(8, -72, 30, -0.5, 1.4);
      ctx.stroke();
    }

    if (airborne) {
      ctx.strokeStyle = "rgba(255,255,255,0.2)";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(-18, 8);
      ctx.lineTo(-2, 18);
      ctx.lineTo(18, 8);
      ctx.stroke();
    }

    if (fighter.hitFlash > 0) {
      ctx.strokeStyle = "rgba(255,255,255,0.75)";
      ctx.lineWidth = 3;
      ctx.strokeRect(-30, -156, 70, 190);
    }
    ctx.restore();
  }

  drawHud() {
    const ctx = this.ctx;
    const drawBar = (x, y, width, value, max, fill, alignRight = false) => {
      ctx.fillStyle = "rgba(7,8,12,0.72)";
      ctx.fillRect(x, y, width, 22);
      const innerWidth = clamp((value / max) * (width - 6), 0, width - 6);
      ctx.fillStyle = fill;
      ctx.fillRect(alignRight ? x + width - 3 - innerWidth : x + 3, y + 3, innerWidth, 16);
      ctx.strokeStyle = "rgba(214,178,96,0.78)";
      ctx.strokeRect(x, y, width, 22);
    };
    const drawPortrait = (fighter, x, y) => {
      ctx.fillStyle = "rgba(7,8,12,0.76)";
      ctx.fillRect(x, y, 86, 86);
      ctx.strokeStyle = `rgb(${fighter.accent.join(",")})`;
      ctx.lineWidth = 3;
      ctx.strokeRect(x, y, 86, 86);
      if (fighter.portraitImage.complete && fighter.portraitImage.naturalWidth > 0) {
        ctx.drawImage(fighter.portraitImage, x + 4, y + 4, 78, 78);
      }
    };
    ctx.fillStyle = "rgba(0,0,0,0.32)";
    ctx.fillRect(18, 14, 486, 102);
    ctx.fillRect(776, 14, 486, 102);
    ctx.strokeStyle = "rgba(214,178,96,0.4)";
    ctx.strokeRect(18, 14, 486, 102);
    ctx.strokeRect(776, 14, 486, 102);
    drawPortrait(this.player, 28, 20);
    drawPortrait(this.enemy, 1166, 20);
    drawBar(126, 28, 370, this.player.health, this.player.maxHealth, "#b84552");
    drawBar(126, 58, 320, this.player.stamina, this.player.maxStamina, "#d6b260");
    drawBar(784, 28, 370, this.enemy.health, this.enemy.maxHealth, "#506dc9", true);
    drawBar(834, 58, 320, this.enemy.stamina, this.enemy.maxStamina, "#d6b260", true);
    ctx.fillStyle = "#f4f0e1";
    ctx.font = "700 24px Georgia";
    ctx.textAlign = "left";
    ctx.fillText(this.player.name, 126, 102);
    ctx.textAlign = "right";
    ctx.fillText(this.enemy.name, 1154, 102);
    ctx.textAlign = "center";
    ctx.font = "700 34px Georgia";
    ctx.fillText(`${this.player.roundWins} - ${this.enemy.roundWins}`, LOGICAL_WIDTH / 2, 48);
    ctx.font = "600 18px Arial";
    ctx.fillText(`ROUND ${this.round}`, LOGICAL_WIDTH / 2, 72);
    ctx.font = "600 14px Arial";
    ctx.textAlign = "left";
    ctx.fillText("VIDA", 126, 22);
    ctx.fillText("STAMINA", 126, 52);
    ctx.textAlign = "right";
    ctx.fillText("VIDA", 1154, 22);
    ctx.fillText("STAMINA", 1154, 52);
  }

  drawOverlayText() {
    if (!this.overlayText) return;
    const ctx = this.ctx;
    ctx.fillStyle = "rgba(0,0,0,0.18)";
    ctx.fillRect(0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT);
    ctx.textAlign = "center";
    ctx.fillStyle = "#111";
    ctx.font = "700 96px Arial";
    ctx.fillText(this.overlayText, LOGICAL_WIDTH / 2 + 6, LOGICAL_HEIGHT / 2 + 6);
    ctx.fillStyle = "#f5e7c4";
    ctx.fillText(this.overlayText, LOGICAL_WIDTH / 2, LOGICAL_HEIGHT / 2);
    if (this.overlaySubtext) {
      ctx.font = "600 26px Arial";
      ctx.fillStyle = "#f4f0e1";
      ctx.fillText(this.overlaySubtext, LOGICAL_WIDTH / 2, LOGICAL_HEIGHT / 2 + 46);
    }
  }
}
