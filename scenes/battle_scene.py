import pygame

from config import HEIGHT, WIDTH
from core.asset_manager import ROOT
from gameplay.card import Card_Item
from gameplay.hand import Hand
from gameplay.terrain import Terrain
from scenes.media_collection import GOLD, INK
from ui.Card_View import CARD_HEIGHT_RATIO, CardView
from ui.terain_ui import TerrainUI


MARGIN = 30
HAND_CARD_WIDTH = 142
HAND_CARD_GAP = 16
HAND_BOTTOM_MARGIN = 132
ARENA_HEIGHT = 1054
SHADOW = (9, 16, 21)
METAL = (23, 36, 40)
METAL_EDGE = (119, 94, 61)
HEALTH_COLOR = (255, 167, 153)
DEMO_PLAYER_HP = 15
DEMO_OPPONENT_HP = 12


class BattleScene:
    def __init__(self, menu):
        self.menu = menu
        self.game = menu.game
        self.back_rect = pygame.Rect(MARGIN, 28, 146, 62)
        self.pass_rect = pygame.Rect(WIDTH - MARGIN - 184, self.back_rect.y, 184, self.back_rect.height)
        self.energy_rect = pygame.Rect((WIDTH - 246) // 2, HEIGHT - 112, 246, 80)
        self.button_font = pygame.font.SysFont("arial", 27, bold=True)
        self.pass_font = pygame.font.SysFont("arial", 34, bold=True)
        self.pointer = (-1, -1)
        self.pass_highlight_until = 0
        self.board = self.make_board()

    def make_board(self):
        terrain = Terrain()
        terrain.place_card(2, Card_Item("vegeta.json", "card_perso"), 0)
        terrain.place_card(2, Card_Item("luffy.json", "card_perso"), 2)
        terrain.place_card(1, Card_Item("macron.json", "card_perso"), 0)
        terrain.place_card(1, Card_Item("creeper.json", "card_perso"), 1)

        hand = Hand()
        hand.add_card(Card_Item("satoru_gojo.json", "card_perso"))
        hand.add_card(Card_Item("ymca.json", "card_ref"))
        hand.add_card(Card_Item("touche_pas_bulma.json", "card_ref"))
        hand.add_card(Card_Item("hi_barbie.json", "card_ref"))

        card_view = CardView()
        terrain_ui = TerrainUI(terrain, card_view)
        board = self.make_arena_background()
        terrain_ui.draw(board, fill_background=False)
        opponent_slot, player_slot = (
            rect for _, index, _, rect in terrain_ui.positions(board.get_size()) if index == 0
        )

        plaque = pygame.image.load(ROOT / "asset/board/plaque.webp")
        for name, hp, size, center_y in (
            ("Adversaire", DEMO_OPPONENT_HP, (384, 88), opponent_slot.top - 44),
            ("Vous", DEMO_PLAYER_HP, (264, 64), player_slot.bottom + 33),
        ):
            plate = pygame.transform.smoothscale(plaque, size)
            board.blit(plate, plate.get_rect(center=(WIDTH // 2, center_y)))
            label = self.button_font.render(name, True, INK)
            health = self.button_font.render(f"{hp} PV", True, HEALTH_COLOR)
            gap = 16
            left = (WIDTH - label.get_width() - gap - health.get_width()) // 2
            label_rect = label.get_rect(midleft=(left, center_y))
            board.blit(label, label_rect)
            board.blit(health, health.get_rect(midleft=(label_rect.right + gap, center_y)))

        card_height = round(HAND_CARD_WIDTH * CARD_HEIGHT_RATIO)
        hand_top = HEIGHT - HAND_BOTTOM_MARGIN - card_height
        hand_width = len(hand.cards) * HAND_CARD_WIDTH + (len(hand.cards) - 1) * HAND_CARD_GAP
        hand_left = (WIDTH - hand_width) // 2
        for index, card in enumerate(hand.cards):
            x = hand_left + index * (HAND_CARD_WIDTH + HAND_CARD_GAP)
            card_view.draw(board, pygame.Rect(x, hand_top, HAND_CARD_WIDTH, card_height), card)

        footer_y = self.energy_rect.top - 13
        pygame.draw.line(board, METAL_EDGE, (MARGIN, footer_y), (WIDTH - MARGIN, footer_y))
        self.draw_energy(board)
        return board

    @staticmethod
    def make_arena_background():
        background = pygame.Surface((WIDTH, HEIGHT))
        background.fill(SHADOW)
        try:
            arena = pygame.image.load(ROOT / "asset/board/theatre-des-echos.webp")
        except (OSError, pygame.error):
            return background

        scale = max(WIDTH / arena.get_width(), ARENA_HEIGHT / arena.get_height())
        size = (round(arena.get_width() * scale), round(arena.get_height() * scale))
        arena = pygame.transform.smoothscale(arena, size)
        background.blit(arena, ((WIDTH - size[0]) // 2, (ARENA_HEIGHT - size[1]) // 2))

        shade = pygame.Surface((WIDTH, ARENA_HEIGHT), pygame.SRCALPHA)
        for y in range(ARENA_HEIGHT):
            top_shade = 168 * max(0, 1 - y / 295)
            bottom_shade = 255 * max(0, (y - 750) / (ARENA_HEIGHT - 1 - 750))
            alpha = round(max(26, top_shade, bottom_shade))
            pygame.draw.line(shade, (*SHADOW, alpha), (0, y), (WIDTH - 1, y))
        background.blit(shade, (0, 0))
        return background

    def draw_energy(self, surface):
        rect = self.energy_rect
        pygame.draw.rect(surface, METAL, rect, border_radius=12)
        pygame.draw.rect(surface, METAL_EDGE, rect, width=1, border_radius=12)
        x, y = rect.left + 29, rect.centery
        gem = [(x, y - 14), (x + 9, y), (x, y + 14), (x - 9, y)]
        pygame.draw.polygon(surface, (142, 205, 205), gem, width=2)
        text = self.button_font.render("Énergie", True, INK)
        surface.blit(text, text.get_rect(midleft=(rect.left + 50, y)))
        value = self.button_font.render("0 / 5", True, GOLD)
        surface.blit(value, value.get_rect(midright=(rect.right - 18, y)))

    @staticmethod
    def draw_label(surface, label, font, color, center):
        text = font.render(label, True, color)
        surface.blit(text, text.get_rect(center=center))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.change_scene(self.menu)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            position = self.menu.to_canvas_position(event.pos)
            if self.back_rect.collidepoint(position):
                self.game.change_scene(self.menu)
            elif self.pass_rect.collidepoint(position):
                self.pass_highlight_until = pygame.time.get_ticks() + 240

    def update(self, dt):
        self.pointer = self.menu.to_canvas_position(pygame.mouse.get_pos())

    def draw(self, surface):
        surface.blit(self.board, (0, 0))
        back_color = (36, 52, 55) if self.back_rect.collidepoint(self.pointer) else METAL
        pygame.draw.rect(surface, back_color, self.back_rect, border_radius=12)
        pygame.draw.rect(surface, METAL_EDGE, self.back_rect, width=2, border_radius=12)
        x, y = self.back_rect.left + 23, self.back_rect.centery
        pygame.draw.lines(surface, GOLD, False, [(x + 6, y - 7), (x, y), (x + 6, y + 7)], 2)
        self.draw_label(surface, "Menu", self.button_font, INK, (self.back_rect.centerx + 9, y))

        pressed = pygame.time.get_ticks() < self.pass_highlight_until
        hovered = self.pass_rect.collidepoint(self.pointer)
        color = (161, 111, 54) if pressed else GOLD if hovered else (203, 152, 75)
        pygame.draw.rect(surface, color, self.pass_rect, border_radius=12)
        pygame.draw.rect(surface, (246, 213, 147), self.pass_rect, width=2, border_radius=12)
        self.draw_label(surface, "Passer", self.pass_font, SHADOW, self.pass_rect.center)
