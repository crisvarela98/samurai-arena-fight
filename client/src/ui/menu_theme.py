import pygame

from src.core.constants import GOLD, GREEN, LIGHT, RED

CHARCOAL = (10, 12, 16)
EBONY = (18, 20, 26)
SLATE = (36, 40, 48)
MIST = (164, 167, 176)
COPPER = (153, 89, 52)
CRIMSON = (151, 36, 36)
MIDNIGHT = (8, 11, 18)
AZURE = (63, 118, 176)

_FONT_CACHE = {}


def get_font(role, size, bold=False):
    families = {
        "display": "georgia",
        "title": "timesnewroman",
        "heading": "bahnschrift",
        "body": "trebuchetms",
        "tiny": "arial",
        "mono": "consolas",
    }
    key = (role, size, bold)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = pygame.font.SysFont(families.get(role, "arial"), size, bold=bold)
    return _FONT_CACHE[key]


def blit_cover(surface, image, target_rect):
    source_width, source_height = image.get_size()
    target_width, target_height = target_rect.size
    scale = max(target_width / source_width, target_height / source_height)
    scaled_size = (max(1, int(source_width * scale)), max(1, int(source_height * scale)))
    scaled = pygame.transform.smoothscale(image, scaled_size)
    x = target_rect.x + (target_width - scaled_size[0]) // 2
    y = target_rect.y + (target_height - scaled_size[1]) // 2
    surface.blit(scaled, (x, y))


def blit_contain(surface, image, target_rect, bottom_align=False):
    source_width, source_height = image.get_size()
    target_width, target_height = target_rect.size
    scale = min(target_width / source_width, target_height / source_height)
    scaled_size = (max(1, int(source_width * scale)), max(1, int(source_height * scale)))
    scaled = pygame.transform.smoothscale(image, scaled_size)
    x = target_rect.x + (target_width - scaled_size[0]) // 2
    y = target_rect.bottom - scaled_size[1] if bottom_align else target_rect.y + (target_height - scaled_size[1]) // 2
    surface.blit(scaled, (x, y))


def _draw_vignette(surface, strength=120):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    width, height = surface.get_size()
    for step in range(8):
        margin = step * 18
        alpha = min(180, strength // 3 + step * 8)
        pygame.draw.rect(
            overlay,
            (0, 0, 0, alpha),
            pygame.Rect(margin, margin, max(0, width - margin * 2), max(0, height - margin * 2)),
            width=22,
            border_radius=26,
        )
    surface.blit(overlay, (0, 0))


def draw_backdrop(surface, image=None, overlay_color=(8, 8, 12, 130), accent_color=(255, 152, 72, 70)):
    surface.fill(MIDNIGHT)
    if image is not None:
        blit_cover(surface, image, surface.get_rect())
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill(overlay_color)
    surface.blit(overlay, (0, 0))

    glow = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(glow, accent_color, (surface.get_width() - 160, 110), 180)
    pygame.draw.circle(glow, (255, 255, 255, 24), (surface.get_width() - 180, 90), 90)
    pygame.draw.circle(glow, (198, 160, 78, 42), (120, surface.get_height() - 110), 150)
    surface.blit(glow, (0, 0))

    grid = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for y in range(0, surface.get_height(), 80):
        pygame.draw.line(grid, (255, 255, 255, 10), (0, y), (surface.get_width(), y), 1)
    for x in range(0, surface.get_width(), 96):
        pygame.draw.line(grid, (255, 255, 255, 6), (x, 0), (x, surface.get_height()), 1)
    surface.blit(grid, (0, 0))
    _draw_vignette(surface)


def draw_panel(surface, rect, accent=GOLD, fill=(10, 12, 17, 214), title=None, title_color=LIGHT):
    shadow = pygame.Surface((rect.width + 24, rect.height + 24), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 74), shadow.get_rect(), border_radius=26)
    surface.blit(shadow, (rect.x - 8, rect.y + 10))

    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=22)
    pygame.draw.rect(panel, (255, 255, 255, 16), panel.get_rect(), 1, border_radius=22)
    pygame.draw.rect(panel, (*accent, 255), panel.get_rect(), 2, border_radius=22)
    pygame.draw.rect(panel, (255, 255, 255, 18), pygame.Rect(16, 16, rect.width - 32, 16), border_radius=8)
    pygame.draw.line(panel, (*accent, 255), (24, 58), (rect.width - 24, 58), 2)
    surface.blit(panel, rect.topleft)

    if title:
        font = get_font("heading", 24, bold=True)
        text = font.render(title, True, title_color)
        surface.blit(text, (rect.x + 24, rect.y + 18))


def draw_chip(surface, rect, text, accent=GOLD, fill=(10, 12, 17, 220), text_color=LIGHT):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=999)
    pygame.draw.rect(panel, (*accent, 255), panel.get_rect(), 2, border_radius=999)
    surface.blit(panel, rect.topleft)
    font = get_font("tiny", 16, bold=True)
    label = font.render(text, True, text_color)
    surface.blit(label, label.get_rect(center=rect.center))


def draw_stat_bar(surface, rect, label, value, maximum, fill_color):
    percentage = 0 if maximum <= 0 else max(0.0, min(1.0, value / maximum))
    track = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(track, (28, 31, 37, 220), track.get_rect(), border_radius=999)
    pygame.draw.rect(track, (255, 255, 255, 18), track.get_rect(), 1, border_radius=999)
    width = max(10, int((rect.width - 4) * percentage))
    pygame.draw.rect(track, fill_color, pygame.Rect(2, 2, width, rect.height - 4), border_radius=999)
    surface.blit(track, rect.topleft)
    font = get_font("tiny", 15, bold=True)
    text = font.render(label, True, LIGHT)
    surface.blit(text, (rect.x, rect.y - 18))


def draw_footer(surface, text, accent=LIGHT):
    font = get_font("tiny", 16)
    label = font.render(text, True, accent)
    surface.blit(label, (28, surface.get_height() - 30))


def draw_stage_label(surface, title, subtitle=None, x=60, y=54):
    title_font = get_font("heading", 38, bold=True)
    surface.blit(title_font.render(title, True, LIGHT), (x, y))
    if subtitle:
        subtitle_font = get_font("body", 20)
        surface.blit(subtitle_font.render(subtitle, True, MIST), (x, y + 46))


def draw_selection_frame(surface, rect, selected=False, accent=GOLD):
    fill = (16, 19, 24, 224) if selected else (10, 12, 17, 204)
    border_color = (*accent, 255) if selected else (*SLATE, 255)
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=18)
    pygame.draw.rect(panel, border_color, panel.get_rect(), 2, border_radius=18)
    if selected:
        pygame.draw.rect(panel, (255, 255, 255, 18), pygame.Rect(12, 12, rect.width - 24, 12), border_radius=999)
    surface.blit(panel, rect.topleft)


def tone_for_result(result):
    if result == "victory":
        return GREEN
    if result == "defeat":
        return RED
    return GOLD
