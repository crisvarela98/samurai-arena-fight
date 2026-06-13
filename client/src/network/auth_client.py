import requests


class AuthClient:
    def __init__(self, server_url, session_storage):
        self.server_url = str(server_url).rstrip("/")
        self.storage = session_storage
        self.session = self.storage.load()
        self.current_user = None

    @property
    def token(self):
        return self.session.get("token")

    @property
    def logged_in(self):
        return bool(self.token)

    def set_server_url(self, server_url):
        self.server_url = str(server_url).rstrip("/")

    def _url(self, path):
        return f"{self.server_url}/{path.lstrip('/')}"

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _request(self, method, path, **kwargs):
        response = requests.request(method, self._url(path), timeout=6.0, **kwargs)
        try:
            payload = response.json()
        except ValueError:
            payload = {"message": response.text or "Respuesta invalida del servidor"}
        if not response.ok:
            raise RuntimeError(payload.get("message", f"Error HTTP {response.status_code}"))
        return payload

    def _store_auth(self, payload):
        user = payload["user"]
        self.session = {
            "token": payload["token"],
            "username": user["username"],
            "user_id": user["id"],
        }
        self.current_user = user
        self.storage.save(payload["token"], user["username"], user["id"])
        return user

    def register(self, username, email, password):
        payload = self._request("POST", "/api/auth/register", json={"username": username, "email": email, "password": password})
        return self._store_auth(payload)

    def login(self, identity, password):
        payload = self._request("POST", "/api/auth/login", json={"identity": identity, "password": password})
        return self._store_auth(payload)

    def get_current_user(self):
        if not self.token:
            return None
        payload = self._request("GET", "/api/auth/me", headers=self._headers())
        self.current_user = payload["user"]
        return self.current_user

    def sync_progress(self, progress, online_fighter=None):
        if not self.token:
            return None
        online_fighter = online_fighter or {}
        payload = self._request(
            "PUT",
            "/api/users/me/progress",
            headers=self._headers(),
            json={
                "storyProgress": progress,
                "coins": progress.get("coins", 0),
                "selectedClan": online_fighter.get("clan_id", "cuervo_negro"),
                "selectedWeapon": online_fighter.get("weapon_id", "katana"),
                "selectedColor": online_fighter.get("color", [170, 48, 52]),
            },
        )
        self.current_user = payload.get("user")
        return self.current_user

    def logout(self):
        if self.token:
            try:
                self._request("POST", "/api/auth/logout", headers=self._headers())
            except Exception:
                pass
        self.session = {}
        self.current_user = None
        self.storage.clear()
