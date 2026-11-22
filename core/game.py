import os
import sys

import pygame
from config import WIDTH, HEIGHT, FPS
from scenes.menu import MenuScene


class Game:
    def __init__(self):
        self.android = sys.platform == "android" or "ANDROID_ARGUMENT" in os.environ
        if self.android:
            os.environ.setdefault("SDL_TOUCH_MOUSE_EVENTS", "0")
            os.environ.setdefault("SDL_ANDROID_TRAP_BACK_BUTTON", "1")
        pygame.init()

        if self.android:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.canvas = pygame.Surface((WIDTH, HEIGHT))

        self.clock = pygame.time.Clock()
        self.running = True

        self.scene = MenuScene(self)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if self.android and event.type == pygame.FINGERDOWN:
            width, height = self.screen.get_size()
            event = pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=1, pos=(int(event.x * width), int(event.y * height))
            )
        elif self.android and event.type == pygame.MOUSEBUTTONDOWN and getattr(event, "touch", False):
            return
        elif self.android and event.type == pygame.KEYDOWN and event.key == pygame.K_AC_BACK:
            event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        self.scene.handle_event(event)

    def change_scene(self, scene):
        self.scene = scene

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, 0.05)

            for event in pygame.event.get():
                self.handle_event(event)

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

        close = getattr(self.scene, "close", None)
        if close is not None:
            close()
        pygame.quit()
