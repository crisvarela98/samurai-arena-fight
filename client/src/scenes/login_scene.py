import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GOLD, GREEN, LIGHT, RED
from src.ui.button import Button
from src.ui.menu_theme import draw_backdrop, draw_panel, get_font
from src.ui.text_input import TextInput


class LoginScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.background = self.game.assets.load_image("assets/ui/menu_online_bg.png", size=(1280, 720))
        self.identity = TextInput((420, 264, 440, 50), "USUARIO O EMAIL")
        self.password = TextInput((420, 350, 440, 50), "CONTRASENA", password=True)
        self.login_button = Button((420, 438, 210, 54), "INGRESAR", variant="primary", font_size=22)
        self.register_button = Button((650, 438, 210, 54), "REGISTRAR", font_size=22)
        self.back_button = Button((42, 42, 140, 46), "VOLVER", variant="ghost", font_size=20)
        self.status = "Online requiere una cuenta activa."
        self.status_color = GOLD

    def _login(self):
        try:
            user = self.game.auth.login(self.identity.text, self.password.text)
            self.game.network.set_auth_token(self.game.auth.token)
            self.game.shared["account_user"] = user
            self.game.shared["online_username"] = user["username"]
            self.game.go(self.game.shared.pop("auth_return_scene", "account"))
        except Exception as exc:
            self.status = str(exc)
            self.status_color = RED

    def handle_event(self, event):
        self.identity.handle_event(event)
        self.password.handle_event(event)
        if event.type != pygame.MOUSEBUTTONUP:
            return
        if self.back_button.rect.collidepoint(event.pos):
            self.game.go("menu")
        elif self.login_button.rect.collidepoint(event.pos):
            self._login()
        elif self.register_button.rect.collidepoint(event.pos):
            self.game.go("register")

    def draw(self, surface):
        draw_backdrop(surface, self.background, overlay_color=(4, 6, 10, 186))
        self.back_button.draw(surface)
        draw_panel(surface, pygame.Rect(350, 132, 580, 444), title="INICIAR SESION")
        surface.blit(get_font("body", 20, bold=True).render("USUARIO O EMAIL", True, LIGHT), (420, 232))
        surface.blit(get_font("body", 20, bold=True).render("CONTRASENA", True, LIGHT), (420, 318))
        self.identity.draw(surface)
        self.password.draw(surface)
        self.login_button.draw(surface, selected=True)
        self.register_button.draw(surface)
        status = get_font("tiny", 18, bold=True).render(self.status, True, self.status_color)
        surface.blit(status, status.get_rect(center=(640, 536)))
