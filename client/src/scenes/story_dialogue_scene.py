import json
from pathlib import Path

import pygame

from src.core.base_scene import BaseScene
from src.core.constants import GOLD, LIGHT
from src.ui.button import Button
from src.ui.menu_theme import draw_backdrop, draw_panel, get_font


class StoryDialogueScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        root = Path(__file__).resolve().parents[2]
        dialogues = json.loads((root / "data" / "story" / "dialogues.json").read_text(encoding="utf-8"))
        self.dialogues = {item["id"]: item for item in dialogues}
        self.background = self.game.assets.load_image("assets/ui/menu_main_bg.png", size=(1280, 720))
        self.continue_button = Button((1000, 602, 210, 48), "CONTINUAR", variant="primary", font_size=20)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP and self.continue_button.rect.collidepoint(event.pos):
            self.game.go(self.game.shared.get("story_dialogue_next", "story_map"))

    def draw(self, surface):
        draw_backdrop(surface, self.background, overlay_color=(0, 0, 0, 190))
        dialogue = self.dialogues.get(self.game.shared.get("story_dialogue_id"), {"speaker": "KENJI", "text": "..."})
        draw_panel(surface, pygame.Rect(90, 438, 1100, 214), title=dialogue["speaker"].upper())
        text = get_font("body", 27).render(dialogue["text"], True, LIGHT)
        surface.blit(text, (132, 520))
        speaker = get_font("heading", 24, bold=True).render(dialogue["speaker"].upper(), True, GOLD)
        surface.blit(speaker, (132, 470))
        self.continue_button.draw(surface, selected=True)
