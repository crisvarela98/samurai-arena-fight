from src.ui.health_bar import draw_bar


def draw_stamina_bar(surface, x, y, width, height, value, maximum):
    draw_bar(surface, x, y, width, height, value, maximum, "STAMINA")
