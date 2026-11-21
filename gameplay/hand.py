
import pygame


class Hand:
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

    def remove_card(self, card):
        if card in self.cards:
            self.cards.remove(card)


class HandUI:
    def __init__(self, hand):
        self.hand = hand
        self.scroll = 0
        self.last_x = None
        self.finger_id = None
        self.cache = {}
        self.cache_size = None

    def _layout(self, size):
        w, h = size
        ch = max(1, min(int(h * 0.24), int(w * 0.55)))
        cw = max(1, int(ch * 0.7))
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

        if self.cache_size != size:
            self.cache.clear()
            self.cache_size = size

        x = zone.x + max(0, (zone.width - total) / 2) - self.scroll

        old_clip = screen.get_clip()
        screen.set_clip(zone)

        for card in self.hand.cards:
            rect = pygame.Rect(int(x), zone.y, cw, ch)

            if rect.colliderect(zone):
                key = id(card)
                if key not in self.cache:
                    self.cache[key] = pygame.transform.smoothscale(
                        card.image, size
                    )
                screen.blit(self.cache[key], rect)

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
