import pygame


CONTROL_BINDINGS = [
    {"key": pygame.K_a, "key_label": "A", "action": "left", "label": "Mover a la izquierda", "mobile_label": "Boton IZQ"},
    {"key": pygame.K_d, "key_label": "D", "action": "right", "label": "Mover a la derecha", "mobile_label": "Boton DER"},
    {"key": pygame.K_w, "key_label": "W", "action": "up", "label": "Saltar", "mobile_label": "Boton SALTO"},
    {"key": pygame.K_s, "key_label": "S", "action": "down", "label": "Agacharse", "mobile_label": "Boton ABAJO"},
    {"key": pygame.K_j, "key_label": "J", "action": "light", "label": "Golpe basico", "mobile_label": "Boton GOLPE"},
    {"key": pygame.K_k, "key_label": "K", "action": "heavy", "label": "Super golpe", "mobile_label": "Boton SUPER"},
    {"key": pygame.K_l, "key_label": "L", "action": "kick", "label": "Patada", "mobile_label": "Boton PATADA"},
    {"key": pygame.K_i, "key_label": "I", "action": "block", "label": "Bloquear", "mobile_label": "Boton BLOQUEO"},
    {"key": pygame.K_o, "key_label": "O", "action": "dodge", "label": "Esquivar", "mobile_label": "Boton ESQUIVA"},
    {"key": pygame.K_ESCAPE, "key_label": "ESC", "action": "pause", "label": "Pausa / salir", "mobile_label": "Boton PAUSA"},
]

PC_CONTROL_ROWS = [(binding["key_label"], binding["label"]) for binding in CONTROL_BINDINGS]
MOBILE_CONTROL_ROWS = [(binding["mobile_label"], binding["label"]) for binding in CONTROL_BINDINGS]
DESKTOP_HINT_TEXT = "A/D mover | W saltar | S agacharse | J golpe | K super | L patada | I bloqueo | O esquiva | ESC pausa"


class InputManager:
    def __init__(self, platform="pc"):
        self.platform = platform
        self.actions = set()
        self.just_pressed = set()
        self.just_released = set()
        self.key_map = {binding["key"]: binding["action"] for binding in CONTROL_BINDINGS}

    def begin_frame(self):
        self.just_pressed.clear()
        self.just_released.clear()

    def set_platform(self, platform):
        self.platform = platform
        self.clear_actions()

    def clear_actions(self):
        self.actions.clear()
        self.just_pressed.clear()
        self.just_released.clear()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.platform == "pc":
            action = self.key_map.get(event.key)
            if action:
                self.actions.add(action)
                self.just_pressed.add(action)
        elif event.type == pygame.KEYUP and self.platform == "pc":
            action = self.key_map.get(event.key)
            if action and action in self.actions:
                self.actions.remove(action)
                self.just_released.add(action)

    def set_action(self, action, pressed):
        if pressed:
            if action not in self.actions:
                self.just_pressed.add(action)
            self.actions.add(action)
        else:
            if action in self.actions:
                self.actions.remove(action)
                self.just_released.add(action)

    def is_down(self, action):
        return action in self.actions

    def was_pressed(self, action):
        return action in self.just_pressed
