import json
import os
from pathlib import Path


class SessionStorage:
    def __init__(self, client_dir):
        client_dir = Path(client_dir)
        android_private = os.environ.get("ANDROID_PRIVATE")
        self.path = Path(android_private) / "session.json" if android_private else client_dir / "data" / "session.json"

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if data.get("token") else {}

    def save(self, token, username, user_id):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"token": token, "username": username, "user_id": user_id}, indent=2),
            encoding="utf-8",
        )

    def clear(self):
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
