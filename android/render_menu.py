import argparse
import os
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame

from config import HEIGHT, WIDTH
from scenes.menu import MenuScene


def render_menu(output: Path) -> None:
    pygame.font.init()
    try:
        canvas = pygame.Surface((WIDTH, HEIGHT))
        MenuScene(None).draw(canvas)
        pygame.image.save(canvas, output)
    finally:
        pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exporte le rendu du menu Pygame.")
    parser.add_argument("output", type=Path)
    render_menu(parser.parse_args().output)
