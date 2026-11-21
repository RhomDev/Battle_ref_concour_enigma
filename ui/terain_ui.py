import pygame


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