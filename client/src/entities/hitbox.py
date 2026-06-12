import pygame


class Hitbox:
    def __init__(self, owner, offset_x, offset_y, width, height):
        self.owner = owner
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.width = width
        self.height = height

    @property
    def rect(self):
        x = self.owner.rect.centerx + (self.offset_x if self.owner.facing == 1 else -self.offset_x - self.width)
        y = self.owner.rect.y + self.offset_y
        return pygame.Rect(x, y, self.width, self.height)
