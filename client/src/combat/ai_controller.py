import random


class AIController:
    def __init__(self):
        self.think_timer = 0.0
        self.block_timer = 0.0

    def update(self, fighter, opponent, dt):
        self.think_timer -= dt
        self.block_timer = max(0.0, self.block_timer - dt)
        if fighter.state == "defeated":
            return {"left": False, "right": False, "light": False, "heavy": False, "kick": False, "block": False, "dodge": False}
        distance = opponent.rect.centerx - fighter.rect.centerx
        actions = {"left": False, "right": False, "light": False, "heavy": False, "kick": False, "block": False, "dodge": False}
        if fighter.health < fighter.stats.max_health * 0.35 and fighter.stamina > 20 and random.random() < 0.015:
            actions["dodge"] = True
            return actions
        if self.think_timer > 0:
            return actions
        self.think_timer = 0.18 + random.random() * 0.12
        if abs(distance) > 130:
            actions["right" if distance > 0 else "left"] = True
        else:
            roll = random.random()
            if roll < 0.28:
                actions["block"] = True
            elif roll < 0.68:
                actions["light"] = True
            else:
                actions["heavy"] = True
        if fighter.health < fighter.stats.max_health * 0.25 and random.random() < 0.2:
            actions["left" if distance > 0 else "right"] = True
        return actions
