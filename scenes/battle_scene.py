from functools import lru_cache

import pygame

from core.asset_manager import AssetManager


FRAMES = {"character": "personnage", "ref": "ref"}
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
                background.blit(image, image.get_rect(center=image_area.center))
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


class TerrainUI:
    def __init__(self, terrain, card_view):
        self.terrain = terrain
        self.card_view = card_view

    def _positions(self, size, local_player):
        width, height = size
        card_width = max(1, round(min(width * .25, height * .25 / 1.5)))
        card_height = max(1, round(card_width * 1.5))
        spacing = round(card_width * .15)
        start_x = (width - 3 * card_width - 2 * spacing) // 2
        opponent = 2 if local_player == 1 else 1
        for player, center_y in ((opponent, height * .28), (local_player, height * .59)):
            for index, card in enumerate(self.terrain.slots[player]):
                rect = pygame.Rect(
                    start_x + index * (card_width + spacing),
                    round(center_y - card_height / 2),
                    card_width,
                    card_height,
                )
                yield player, index, card, rect

    def get_clicked_card(self, position, size, local_player=1):
        for player, index, card, rect in self._positions(size, local_player):
            if card is not None and rect.collidepoint(position):
                return card, player, index
        return None, None, None

    def draw(self, surface, local_player=1):
        surface.fill((20, 24, 36))
        for _, _, card, rect in self._positions(surface.get_size(), local_player):
            if card is None:
                pygame.draw.rect(surface, (29, 35, 51), rect, border_radius=10)
            else:
                self.card_view.draw(surface, rect, card)


class HandUI:
    def __init__(self, hand, card_view):
        self.hand = hand
        self.card_view = card_view
        self.scroll = 0
        self.last_x = None
        self.finger_id = None

    def _layout(self, size):
        w, h = size
        ch = max(1, min(int(h * 0.24), int(w * 0.55)))
        cw = max(1, round(ch / 1.5))
        gap = max(6, cw // 10)
        margin = max(8, w // 50)

        zone = pygame.Rect(margin, h - ch - margin, w - 2 * margin, ch)

        total = max(0, len(self.hand.cards) * (cw + gap) - gap)
        limit = max(0, total - zone.width)
        self.scroll = max(0, min(self.scroll, limit))

        return zone, (cw, ch), gap, total, limit

    def _move(self, dx, limit):
        self.scroll = max(0, min(self.scroll + dx, limit))

    def draw(self, screen):
        zone, size, gap, total, _ = self._layout(screen.get_size())
        cw, ch = size

        x = zone.x + max(0, (zone.width - total) / 2) - self.scroll

        old_clip = screen.get_clip()
        screen.set_clip(zone)

        for card in self.hand.cards:
            rect = pygame.Rect(int(x), zone.y, cw, ch)

            if rect.colliderect(zone):
                self.card_view.draw(screen, rect, card)

            x += cw + gap

        screen.set_clip(old_clip)

    def handle_event(self, event, size):
        zone, (cw, _), _, _, limit = self._layout(size)

        # Molette PC
        if event.type == pygame.MOUSEWHEEL:
            if zone.collidepoint(pygame.mouse.get_pos()):
                self._move((event.x - event.y) * cw, limit)

        # Souris
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and not getattr(event, "touch", False):
                if zone.collidepoint(event.pos):
                    self.last_x = event.pos[0]

        elif event.type == pygame.MOUSEMOTION:
            if self.last_x is not None and self.finger_id is None:
                if not getattr(event, "touch", False):
                    self._move(self.last_x - event.pos[0], limit)
                    self.last_x = event.pos[0]

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.finger_id is None:
                self.last_x = None

        # Tactile Android
        elif event.type == pygame.FINGERDOWN:
            x, y = event.x * size[0], event.y * size[1]
            if self.finger_id is None and zone.collidepoint(x, y):
                self.finger_id = event.finger_id
                self.last_x = x

        elif event.type == pygame.FINGERMOTION:
            if event.finger_id == self.finger_id:
                x = event.x * size[0]
                self._move(self.last_x - x, limit)
                self.last_x = x

        elif event.type == pygame.FINGERUP:
            if event.finger_id == self.finger_id:
                self.finger_id = None
                self.last_x = None
