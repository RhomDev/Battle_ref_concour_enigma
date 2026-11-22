import pygame

from core.asset_manager import ROOT


def interface_font(size, *, bold=False):
    filename = "FreeSansBold.ttf" if bold else "FreeSans.ttf"
    return pygame.font.Font(ROOT / "asset" / "fonts" / filename, size)
