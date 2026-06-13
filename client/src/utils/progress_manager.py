import json
import os
from copy import deepcopy
from pathlib import Path


DEFAULT_PROGRESS = {
    "first_time_completed": False,
    "story_act": 1,
    "story_mission": 0,
    "completed_missions": [],
    "unlocked_modes": ["Historia"],
    "coins": 0,
    "unlocked_weapons": ["katana"],
    "unlocked_clans": ["cuervo_negro"],
    "selected_story_character": "kenji",
}


class ProgressManager:
    def __init__(self, client_dir):
        self.client_dir = Path(client_dir)
        self.template_path = self.client_dir / "data" / "progress.json"
        android_private = os.environ.get("ANDROID_PRIVATE")
        self.path = Path(android_private) / "progress.json" if android_private else self.template_path
        self.data = self.load()

    def load(self):
        source = self.path if self.path.exists() else self.template_path
        try:
            loaded = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            loaded = {}
        progress = deepcopy(DEFAULT_PROGRESS)
        progress.update(loaded)
        return progress

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    def mission_unlocked(self, mission_number):
        return mission_number <= min(6, int(self.data.get("story_mission", 0)) + 1)

    def complete_mission(self, mission_number, reward_coins=0):
        completed = set(self.data.get("completed_missions", []))
        first_completion = mission_number not in completed
        completed.add(mission_number)
        self.data["completed_missions"] = sorted(completed)
        self.data["story_act"] = 1
        self.data["story_mission"] = max(int(self.data.get("story_mission", 0)), mission_number)
        if first_completion:
            self.data["coins"] = int(self.data.get("coins", 0)) + int(reward_coins)
        if mission_number == 1:
            self.data["first_time_completed"] = True
            self.data["unlocked_modes"] = ["Historia", "Online"]
        self.save()
        return first_completion
