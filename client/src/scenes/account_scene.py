import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GOLD, GREEN, LIGHT, RED
from src.ui.button import Button
from src.ui.menu_theme import draw_backdrop, draw_chip, draw_panel, get_font


class AccountScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.background = self.game.assets.load_image("assets/ui/menu_online_bg.png", size=(1280, 720))
        self.login_button = Button((410, 490, 220, 54), "INICIAR SESION", variant="primary", font_size=21)
        self.register_button = Button((650, 490, 220, 54), "REGISTRARSE", font_size=21)
        self.logout_button = Button((530, 510, 220, 54), "CERRAR SESION", variant="danger", font_size=21)
        self.back_button = Button((42, 42, 140, 46), "VOLVER", variant="ghost", font_size=20)
        self.user = None
        self.status = ""

    def on_enter(self):
        self.user = self.game.shared.get("account_user")
        if self.game.auth.logged_in:
            try:
                self.user = self.game.auth.get_current_user()
                self.game.shared["account_user"] = self.user
                self.status = "Datos sincronizados con el servidor."
            except Exception as exc:
                self.status = str(exc)

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONUP:
            return
        if self.back_button.rect.collidepoint(event.pos):
            self.game.go("menu")
        elif not self.game.auth.logged_in and self.login_button.rect.collidepoint(event.pos):
            self.game.go("login")
        elif not self.game.auth.logged_in and self.register_button.rect.collidepoint(event.pos):
            self.game.go("register")
        elif self.game.auth.logged_in and self.logout_button.rect.collidepoint(event.pos):
            self.game.network.disconnect()
            self.game.auth.logout()
            self.game.network.set_auth_token(None)
            self.game.shared["account_user"] = None
            self.user = None
            self.status = "Sesion cerrada."

    def draw(self, surface):
        draw_backdrop(surface, self.background, overlay_color=(4, 6, 10, 184))
        self.back_button.draw(surface)
        draw_panel(surface, pygame.Rect(320, 126, 640, 468), title="CUENTA")
        if self.game.auth.logged_in and self.user:
            title = get_font("display", 46, bold=True).render(self.user["username"].upper(), True, GOLD)
            surface.blit(title, title.get_rect(center=(640, 230)))
            draw_chip(surface, pygame.Rect(438, 292, 180, 34), f"VICTORIAS {self.user.get('wins', 0)}", accent=GREEN)
            draw_chip(surface, pygame.Rect(662, 292, 180, 34), f"DERROTAS {self.user.get('losses', 0)}", accent=RED)
            draw_chip(surface, pygame.Rect(510, 354, 260, 34), f"RANKING {self.user.get('rankingPoints', 0)}")
            email = get_font("body", 22).render(self.user.get("email", ""), True, LIGHT)
            surface.blit(email, email.get_rect(center=(640, 420)))
            self.logout_button.draw(surface)
        else:
            message = get_font("body", 25).render("No hay una sesion iniciada.", True, LIGHT)
            surface.blit(message, message.get_rect(center=(640, 300)))
            self.login_button.draw(surface, selected=True)
            self.register_button.draw(surface)
        if self.status:
            status = get_font("tiny", 17).render(self.status, True, LIGHT)
            surface.blit(status, status.get_rect(center=(640, 570)))
