from functools import lru_cache

import pygame

from core.asset_manager import AssetManager


FRAMES = {"character": "personnage", "ref": "ref"}
CARD_HEIGHT_RATIO = 1.5
EFFECT_LABELS = {"attack": "Attaque", "heal": "Soin", "shield": "Bouclier"}
TITLE_COLOR = (255, 240, 214)
BODY_COLOR = (53, 36, 32)
COST_FILL = (18, 43, 48)
COST_EDGE = (124, 199, 205)
HP_FILL = (86, 27, 36)
HP_EDGE = (244, 144, 136)


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

    def _label(self, surface, text, rect, y, *, x=.5, max_width=.84, color=BODY_COLOR, font=None):
        if font is None:
            font = self._font(max(11, round(rect.height * .088)))
        width = rect.width * max_width
        if font.size(text)[0] > width:
            while text and font.size(text + "…")[0] > width:
                text = text[:-1]
            text += "…"
        label = font.render(text, True, color)
        center = (round(rect.x + rect.width * x), round(rect.y + rect.height * y))
        surface.blit(label, label.get_rect(center=center))

    def _stat_badge(self, surface, rect, x, value, fill, edge):
        center = (round(rect.x + rect.width * x), round(rect.y + rect.height * .13))
        radius = max(1, round(rect.width * .09))
        pygame.draw.circle(surface, fill, center, radius)
        pygame.draw.circle(surface, edge, center, radius, width=1)
        self._label(surface, str(value), rect, .13, x=x, max_width=.17, color=TITLE_COLOR)

    def _character_name(self, surface, rect, name):
        font = self._font(max(11, round(rect.height * .078)))
        max_width = .49
        if font.size(name)[0] <= rect.width * max_width or " " not in name:
            lines = ((name, .13),)
        else:
            words = name.split()
            split = len(words) - 1
            while split > 1 and font.size(" ".join(words[:split]))[0] > rect.width * max_width:
                split -= 1
            lines = ((" ".join(words[:split]), .098), (" ".join(words[split:]), .158))
        for line, y in lines:
            self._label(surface, line, rect, y, max_width=max_width, color=TITLE_COLOR, font=font)

    def draw(self, surface, rect, card):
        surface.blit(self._background(card.type, card.media, rect.size), rect)
        if card.type == "character":
            self._stat_badge(surface, rect, .16, card.cost, COST_FILL, COST_EDGE)
            self._stat_badge(surface, rect, .84, card.hp, HP_FILL, HP_EDGE)
            self._character_name(surface, rect, card.name)
            if card.hp < card.hp_max:
                self._label(surface, f"PV max. {card.hp_max}", rect, .76)
            if card.shield:
                self._label(surface, f"Bouclier {card.shield}", rect, .88)
        else:
            self._label(surface, str(card.cost), rect, .13, x=.16, max_width=.16, color=TITLE_COLOR)
            self._label(surface, card.name, rect, .13, x=.61, max_width=.66, color=TITLE_COLOR)
            self._label(surface, f"{EFFECT_LABELS[card.effect_type]} {card.amount}", rect, .77)

