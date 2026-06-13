import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GOLD, LIGHT, RED
from src.ui.button import Button
from src.ui.menu_theme import draw_backdrop, draw_panel, get_font
from src.ui.text_input import TextInput


class RegisterScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.background = self.game.assets.load_image("assets/ui/menu_online_bg.png", size=(1280, 720))
        self.username = TextInput((420, 224, 440, 48), "USUARIO", max_length=24)
        self.email = TextInput((420, 304, 440, 48), "EMAIL")
        self.password = TextInput((420, 384, 440, 48), "CONTRASENA", password=True)
        self.submit_button = Button((420, 470, 210, 54), "CREAR CUENTA", variant="primary", font_size=20)
        self.login_button = Button((650, 470, 210, 54), "YA TENGO CUENTA", font_size=18)
        self.back_button = Button((42, 42, 140, 46), "VOLVER", variant="ghost", font_size=20)
        self.status = "Minimo 3 caracteres de usuario y 6 de contrasena."
        self.status_color = GOLD

    def _register(self):
        try:
            user = self.game.auth.register(self.username.text, self.email.text, self.password.text)
            self.game.network.set_auth_token(self.game.auth.token)
            self.game.shared["account_user"] = user
            self.game.shared["online_username"] = user["username"]
            self.game.go(self.game.shared.pop("auth_return_scene", "account"))
        except Exception as exc:
            self.status = str(exc)
            self.status_color = RED

    def handle_event(self, event):
        for field in (self.username, self.email, self.password):
            field.handle_event(event)
        if event.type != pygame.MOUSEBUTTONUP:
            return
        if self.back_button.rect.collidepoint(event.pos):
            self.game.go("login")
        elif self.submit_button.rect.collidepoint(event.pos):
            self._register()
        elif self.login_button.rect.collidepoint(event.pos):
            self.game.go("login")

    def draw(self, surface):
        draw_backdrop(surface, self.background, overlay_color=(4, 6, 10, 186))
        self.back_button.draw(surface)
        draw_panel(surface, pygame.Rect(350, 108, 580, 486), title="CREAR CUENTA")
        labels = (("USUARIO", 194), ("EMAIL", 274), ("CONTRASENA", 354))
        for label, y in labels:
            surface.blit(get_font("body", 19, bold=True).render(label, True, LIGHT), (420, y))
        self.username.draw(surface)
        self.email.draw(surface)
        self.password.draw(surface)
        self.submit_button.draw(surface, selected=True)
        self.login_button.draw(surface)
        status = get_font("tiny", 17, bold=True).render(self.status, True, self.status_color)
        surface.blit(status, status.get_rect(center=(640, 558)))
