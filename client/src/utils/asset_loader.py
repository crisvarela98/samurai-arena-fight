from pathlib import Path

import pygame


class AssetLoader:
    def __init__(self, root):
        self.root = Path(root)
        self.images = {}
        self.sprite_strips = {}
        self.sounds = {}
        self.fonts = {}

    def load_image(self, relative_path, size=None, trim_alpha=False, chroma_key=None, chroma_tolerance=0, despill=False):
        key = (str(relative_path), size, trim_alpha, chroma_key, chroma_tolerance, despill)
        if key in self.images:
            return self.images[key]
        path = self.root / relative_path
        if path.exists():
            image = pygame.image.load(str(path)).convert_alpha()
        else:
            image = pygame.Surface(size or (64, 64), pygame.SRCALPHA)
            image.fill((120, 30, 30))
        if chroma_key is not None:
            image = self._remove_chroma(image, chroma_key, chroma_tolerance)
            if despill:
                image = self._despill_key(image, chroma_key)
        if trim_alpha:
            bounds = image.get_bounding_rect(min_alpha=1)
            if bounds.width and bounds.height:
                image = image.subsurface(bounds).copy()
        if size:
            image = pygame.transform.smoothscale(image, size)
        self.images[key] = image
        return image

    def load_sprite_strip(self, relative_path, frame_count, scale_height=None, chroma_key=None, chroma_tolerance=0, despill=False):
        key = (str(relative_path), frame_count, scale_height, chroma_key, chroma_tolerance, despill)
        if key in self.sprite_strips:
            return self.sprite_strips[key]

        sheet = self.load_image(
            relative_path,
            chroma_key=chroma_key,
            chroma_tolerance=chroma_tolerance,
            despill=despill,
        )
        frame_width = sheet.get_width() // frame_count
        frames = []

        for index in range(frame_count):
            frame = pygame.Surface((frame_width, sheet.get_height()), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), pygame.Rect(index * frame_width, 0, frame_width, sheet.get_height()))
            bounds = frame.get_bounding_rect(min_alpha=1)
            if bounds.width and bounds.height:
                frame = frame.subsurface(bounds).copy()
            if scale_height and frame.get_height() > 0:
                scale = scale_height / frame.get_height()
                target_size = (max(1, int(frame.get_width() * scale)), scale_height)
                frame = pygame.transform.smoothscale(frame, target_size)
            frames.append(frame)

        self.sprite_strips[key] = frames
        return frames

    def _remove_chroma(self, image, chroma_key, tolerance):
        cleaned = image.copy()
        width, height = cleaned.get_size()
        red_key, green_key, blue_key = chroma_key

        for y in range(height):
            for x in range(width):
                red, green, blue, alpha = cleaned.get_at((x, y))
                if (
                    abs(red - red_key) <= tolerance
                    and abs(green - green_key) <= tolerance
                    and abs(blue - blue_key) <= tolerance
                ):
                    cleaned.set_at((x, y), (red, green, blue, 0))
                else:
                    cleaned.set_at((x, y), (red, green, blue, alpha))

        return cleaned

    def _despill_key(self, image, chroma_key):
        cleaned = image.copy()
        width, height = cleaned.get_size()
        key_red, key_green, key_blue = chroma_key

        for y in range(height):
            for x in range(width):
                red, green, blue, alpha = cleaned.get_at((x, y))
                if alpha == 0:
                    continue
                dominant_key = green if key_green >= max(key_red, key_blue) else max(key_red, key_blue)
                if dominant_key == green:
                    if green <= max(red, blue) + 28:
                        continue
                    if green > 140 and red < 96 and blue < 96:
                        cleaned.set_at((x, y), (0, 0, 0, 0))
                        continue
                    cleaned.set_at((x, y), (red, max(red, blue), blue, alpha))

        return cleaned
