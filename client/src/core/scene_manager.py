class SceneManager:
    def __init__(self, game):
        self.game = game
        self.current_scene = None
        self.overlay_scene = None

    def change(self, scene):
        if self.current_scene:
            self.current_scene.on_exit()
        self.current_scene = scene
        self.current_scene.on_enter()

    def push(self, scene):
        self.overlay_scene = scene
        self.overlay_scene.on_enter()

    def pop(self):
        if self.overlay_scene:
            self.overlay_scene.on_exit()
            self.overlay_scene = None

    def handle_event(self, event):
        if self.overlay_scene:
            self.overlay_scene.handle_event(event)
            return
        if self.current_scene:
            self.current_scene.handle_event(event)

    def update(self, dt):
        if self.overlay_scene:
            self.overlay_scene.update(dt)
            return
        if self.current_scene:
            self.current_scene.update(dt)

    def draw(self, surface):
        if self.current_scene:
            self.current_scene.draw(surface)
        if self.overlay_scene:
            self.overlay_scene.draw(surface)
