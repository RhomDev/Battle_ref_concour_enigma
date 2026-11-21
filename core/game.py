import pygame
from config import WIDTH, HEIGHT, FPS
from scenes.menu import MenuScene


class Game:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT), pygame.RESIZABLE
        )
        self.canvas = pygame.Surface((WIDTH, HEIGHT))

        self.clock = pygame.time.Clock()
        self.running = True

        self.scene = MenuScene(self)

    def change_scene(self, scene):
        self.scene = scene

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.scene.handle_event(event)

            self.scene.update(dt)

            self.canvas.fill((25, 30, 45))
            self.scene.draw(self.canvas)

            # Adaptation à la taille de la fenêtre
            window_w, window_h = self.screen.get_size()

            scale = min(
                window_w / WIDTH,
                window_h / HEIGHT
            )

            new_size = (
                int(WIDTH * scale),
                int(HEIGHT * scale)
            )

            scaled = pygame.transform.scale(
                self.canvas, new_size
            )

            self.screen.fill((0, 0, 0))

            x = (window_w - new_size[0]) // 2
            y = (window_h - new_size[1]) // 2

            self.screen.blit(scaled, (x, y))
            pygame.display.flip()

        pygame.quit()