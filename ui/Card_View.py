from functools import lru_cache

import pygame

from core.asset_manager import AssetManager


FRAMES = {"character": "personnage", "ref": "ref"}
CARD_HEIGHT_RATIO = 1.5
EFFECT_LABELS = {"attack": "Attaque", "heal": "Soin", "shield": "Bouclier"}
TITLE_COLOR = (255, 240, 214)
BODY_COLOR = (53, 36, 32)


class CardView:
    def __init__(self, assets=None):
        self.assets = assets if assets is not None else AssetManager()

    @lru_cache(maxsize=64)
    def _background(self, kind, media_ids, size):
        width, height = size
        image_area = pygame.Rect(
            round(width * .05),
            round(height * .20),
            round(width * .90),
            round(height * .50),
        )
        background = pygame.Surface(size, pygame.SRCALPHA)
        background.fill((39, 28, 35), image_area)

        photo = self.assets.media_for(media_ids)["image"]
        if photo and image_area.width and image_area.height:
            try:
                image = self.assets.load_image(photo["localPath"])
                scale = max(image_area.width / image.get_width(), image_area.height / image.get_height())
                image = pygame.transform.smoothscale(
                    image, (round(image.get_width() * scale), round(image.get_height() * scale))
                )
                background.set_clip(image_area)
                background.blit(image, image.get_rect(midtop=image_area.midtop))
                background.set_clip(None)
            except (OSError, pygame.error):
                pass

        frame = self.assets.load_image(f"asset/frames/{FRAMES[kind]}.png")
        background.blit(pygame.transform.smoothscale(frame, size), (0, 0))
        return background

    @staticmethod
    @lru_cache(maxsize=32)
    def _font(size):
        return pygame.font.Font(None, size)

    def _label(self, surface, text, rect, y, *, x=.5, max_width=.84, color=BODY_COLOR):
        font = self._font(max(11, round(rect.height * .088)))
        width = rect.width * max_width
        if font.size(text)[0] > width:
            while text and font.size(text + "…")[0] > width:
                text = text[:-1]
            text += "…"
        label = font.render(text, True, color)
        center = (round(rect.x + rect.width * x), round(rect.y + rect.height * y))
        surface.blit(label, label.get_rect(center=center))

    def draw(self, surface, rect, card):
        surface.blit(self._background(card.type, card.media, rect.size), rect)
        self._label(surface, str(card.cost), rect, .13, x=.16, max_width=.16, color=TITLE_COLOR)
        self._label(surface, card.name, rect, .13, x=.61, max_width=.66, color=TITLE_COLOR)
        if card.type == "character":
            self._label(surface, f"{card.hp}/{card.hp_max} PV", rect, .76)
            if card.shield:
                self._label(surface, f"Bouclier {card.shield}", rect, .88)
        else:
            self._label(surface, f"{EFFECT_LABELS[card.effect_type]} {card.amount}", rect, .77)

