import pygame

from ui.Card_View import CARD_HEIGHT_RATIO


BACKGROUND = (20, 24, 36)
CARD_WIDTH_RATIO = 0.25
MAX_CARD_HEIGHT_RATIO = 0.25
SLOT_GAP_RATIO = 0.15
OPPONENT_ROW_Y = 0.26
PLAYER_ROW_Y = 0.57


class TerrainUI:
    def __init__(self, terrain, card_view):
        self.terrain = terrain
        self.card_view = card_view

    def positions(self, size, local_player=1):
        width, height = size
        max_card_width = min(width * CARD_WIDTH_RATIO, height * MAX_CARD_HEIGHT_RATIO / CARD_HEIGHT_RATIO)
        card_width = max(1, round(max_card_width))
        card_height = round(card_width * CARD_HEIGHT_RATIO)
        spacing = round(card_width * SLOT_GAP_RATIO)
        start_x = (width - 3 * card_width - 2 * spacing) // 2
        opponent = 2 if local_player == 1 else 1
        for player, center_y in ((opponent, height * OPPONENT_ROW_Y), (local_player, height * PLAYER_ROW_Y)):
            for index, card in enumerate(self.terrain.slots[player]):
                rect = pygame.Rect(
                    start_x + index * (card_width + spacing),
                    round(center_y - card_height / 2),
                    card_width,
                    card_height,
                )
                yield player, index, card, rect

    def get_clicked_card(self, position, size, local_player=1):
        for player, index, card, rect in self.positions(size, local_player):
            if card is not None and rect.collidepoint(position):
                return card, player, index
        return None, None, None

    def get_slot_at(self, position, size, local_player=1):
        for player, index, card, rect in self.positions(size, local_player):
            if rect.collidepoint(position):
                return player, index, card, rect
        return None, None, None, None

    def draw(self, surface, local_player=1, *, fill_background=True):
        if fill_background:
            surface.fill(BACKGROUND)
        for _, _, card, rect in self.positions(surface.get_size(), local_player):
            if card is None:
                self.draw_empty_slot(surface, rect)
            else:
                self.card_view.draw(surface, rect, card)

    @staticmethod
    def draw_empty_slot(surface, rect):
        slot = pygame.Surface(rect.size, pygame.SRCALPHA)
        frame = slot.get_rect().inflate(-12, -16)
        trim = (205, 172, 108, 165)
        pygame.draw.rect(slot, (9, 19, 22, 95), frame, border_radius=10)
        pygame.draw.rect(slot, (205, 172, 108, 85), frame, width=1, border_radius=10)
        for x, dx in ((frame.left + 5, 1), (frame.right - 6, -1)):
            for y, dy in ((frame.top + 5, 1), (frame.bottom - 6, -1)):
                pygame.draw.lines(slot, trim, False, [(x, y + dy * 20), (x, y), (x + dx * 20, y)], 2)
        x, y = frame.center
        pygame.draw.polygon(slot, trim, [(x, y - 11), (x + 11, y), (x, y + 11), (x - 11, y)], 1)
        surface.blit(slot, rect)
