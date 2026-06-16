import random


class AIController:
    def __init__(self):
        self.think_timer = 0.0
        self.block_timer = 0.0
        self.move_direction = 0

    @staticmethod
    def _idle_actions():
        return {
            "left": False,
            "right": False,
            "up": False,
            "down": False,
            "light": False,
            "heavy": False,
            "kick": False,
            "kick_type": None,
            "block": False,
            "dodge": False,
        }

    def update(self, fighter, opponent, dt):
        self.think_timer -= dt
        self.block_timer = max(0.0, self.block_timer - dt)
        if fighter.state == "defeated":
            return self._idle_actions()
        distance = opponent.rect.centerx - fighter.rect.centerx
        actions = self._idle_actions()
        actions["left"] = self.move_direction < 0
        actions["right"] = self.move_direction > 0
        actions["block"] = self.block_timer > 0
        if opponent.state in {"attack_light", "attack_heavy", "kick", "low_kick", "flying_kick"} and abs(distance) < 130:
            if fighter.stamina > 18 and random.random() < 0.025:
                actions["dodge"] = True
                return actions
            self.block_timer = max(self.block_timer, 0.22)
            actions["block"] = True
        if fighter.health < fighter.stats.max_health * 0.35 and fighter.stamina > 20 and random.random() < 0.015:
            actions["dodge"] = True
            return actions
        if self.think_timer > 0:
            return actions
        self.think_timer = 0.12 + random.random() * 0.10
        if abs(distance) > 150:
            self.move_direction = 1 if distance > 0 else -1
        else:
            self.move_direction = 0
            actions["left"] = False
            actions["right"] = False
            roll = random.random()
            if roll < 0.22:
                self.block_timer = 0.24 + random.random() * 0.18
                actions["block"] = True
            elif roll < 0.56:
                actions["light"] = True
            elif roll < 0.82:
                actions["kick"] = True
                if fighter.on_ground and abs(distance) < 104 and random.random() < 0.42:
                    actions["down"] = True
                    actions["kick_type"] = "low_kick"
                elif fighter.on_ground and abs(distance) < 136 and random.random() < 0.28:
                    actions["up"] = True
                    actions["kick_type"] = "flying_kick"
                else:
                    actions["kick_type"] = "kick"
            else:
                actions["heavy"] = True
        if fighter.on_ground and abs(distance) > 150 and abs(distance) < 260 and fighter.stamina > 14 and random.random() < 0.05:
            actions["up"] = True
        if fighter.health < fighter.stats.max_health * 0.25 and random.random() < 0.2:
            self.move_direction = -1 if distance > 0 else 1
            actions["left"] = self.move_direction < 0
            actions["right"] = self.move_direction > 0
        return actions
