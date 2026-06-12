import pygame

from src.core.constants import GOLD, GREEN, LIGHT, RED


def draw_bar(surface, x, y, width, height, value, maximum, label, fill_color=None):
    ratio = 0 if maximum <= 0 else max(0.0, min(1.0, value / maximum))
    fill_color = fill_color or (GREEN if label == "STAMINA" else RED)

    shadow_rect = pygame.Rect(x, y + 4, width, height)
    pygame.draw.rect(surface, (0, 0, 0, 76), shadow_rect, border_radius=12)

    track = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(track, (12, 14, 18, 228), track.get_rect(), border_radius=12)
    pygame.draw.rect(track, (255, 255, 255, 18), track.get_rect(), 1, border_radius=12)
    pygame.draw.rect(track, (255, 255, 255, 16), pygame.Rect(8, 6, width - 16, max(4, height // 3)), border_radius=999)
    fill_width = max(8, int((width - 4) * ratio)) if ratio > 0 else 0
    if fill_width:
        pygame.draw.rect(track, fill_color, pygame.Rect(2, 2, fill_width, height - 4), border_radius=10)
        highlight_width = max(6, fill_width - 14)
        pygame.draw.rect(
            track,
            (255, 255, 255, 34),
            pygame.Rect(6, 5, highlight_width, max(4, height // 3)),
            border_radius=999,
        )
    surface.blit(track, (x, y))

    label_font = pygame.font.SysFont("bahnschrift", 20, bold=True)
    value_font = pygame.font.SysFont("arial", 16, bold=True)
    text = label_font.render(label, True, LIGHT)
    value_text = value_font.render(f"{int(value)}/{int(maximum)}", True, GOLD if label != "STAMINA" else LIGHT)
    surface.blit(text, (x + 8, y - 24))
    surface.blit(value_text, (x + width - value_text.get_width() - 10, y - 22))


def draw_portrait_badge(surface, rect, portrait, accent=GOLD, flip=False):
    shadow = pygame.Surface((rect.width + 10, rect.height + 12), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 86), shadow.get_rect(), border_radius=24)
    surface.blit(shadow, (rect.x - 5, rect.y + 6))

    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (9, 11, 16, 238), panel.get_rect(), border_radius=22)
    pygame.draw.rect(panel, (*accent, 255), panel.get_rect(), 2, border_radius=22)
    pygame.draw.rect(panel, (255, 255, 255, 16), pygame.Rect(10, 10, rect.width - 20, 10), border_radius=999)
    pygame.draw.circle(panel, (*accent, 40), (rect.width // 2, rect.height // 2 + 4), rect.width // 2 - 14)
    surface.blit(panel, rect.topleft)

    if portrait is None:
        return

    image = pygame.transform.flip(portrait, True, False) if flip else portrait
    clip_rect = rect.inflate(-12, -12)
    scale = max(clip_rect.width / image.get_width(), clip_rect.height / image.get_height())
    scaled_size = (max(1, int(image.get_width() * scale)), max(1, int(image.get_height() * scale)))
    scaled = pygame.transform.smoothscale(image, scaled_size)
    image_rect = scaled.get_rect(midtop=(rect.centerx, rect.y + 4))
    shadow_tint = pygame.mask.from_surface(scaled).to_surface(
        setcolor=(0, 0, 0, 70),
        unsetcolor=(0, 0, 0, 0),
    ).convert_alpha()

    previous_clip = surface.get_clip()
    surface.set_clip(clip_rect)
    for offset_x, offset_y in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        surface.blit(shadow_tint, image_rect.move(offset_x, offset_y))
    surface.blit(scaled, image_rect)
    surface.set_clip(previous_clip)
