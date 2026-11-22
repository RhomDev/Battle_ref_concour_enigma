from copy import copy

import pygame

from config import HEIGHT, WIDTH
from core.asset_manager import ROOT
from gameplay.terrain import Terrain
from scenes.media_collection import GOLD, INK
from ui.Card_View import CARD_HEIGHT_RATIO, CardView
from ui.terain_ui import TerrainUI
from ui.fonts import interface_font


MARGIN = 30
HAND_CARD_WIDTH = 142
HAND_CARD_GAP = 16
HAND_BOTTOM_MARGIN = 144
CARDS_PER_PAGE = 4
ARENA_HEIGHT = 1054
SHADOW = (9, 16, 21)
METAL = (23, 36, 40)
METAL_EDGE = (119, 94, 61)
HEALTH_COLOR = (255, 167, 153)


class BattleScene:
    def __init__(self, lobby, session, state):
        self.lobby = lobby
        self.menu = lobby.menu
        self.game = lobby.game
        self.session = session
        self.back_rect = pygame.Rect(MARGIN, 28, 146, 62)
        self.pass_rect = pygame.Rect(WIDTH - MARGIN - 184, 28, 184, 62)
        self.energy_rect = pygame.Rect(MARGIN, HEIGHT - 105, 250, 72)
        self.draw_rect = pygame.Rect(WIDTH - MARGIN - 245, HEIGHT - 105, 245, 72)
        self.prev_rect = pygame.Rect(40, 1140, 136, 30)
        self.next_rect = pygame.Rect(WIDTH - 176, 1140, 136, 30)
        self.button_font = interface_font(27, bold=True)
        self.small_font = interface_font(23)
        self.pointer = (-1, -1)
        self.background = self.make_arena_background()
        self.plaque = pygame.image.load(ROOT / "asset/board/plaque.webp").convert_alpha()
        self.terrain = Terrain()
        self.card_view = CardView()
        self.terrain_ui = TerrainUI(self.terrain, self.card_view)
        self.page = 0
        self.selected = None
        self.pending = False
        self.notice = ""
        self.set_state(state)

    def close(self):
        self.session.close()

    def leave(self, notice=""):
        self.close()
        self.lobby.return_with_notice(notice)
        self.game.change_scene(self.lobby)

    def set_state(self, state):
        self.state = state
        self.seat = state["seat"]
        self.opponent = 3 - self.seat
        for player in state["players"]:
            self.terrain.slots[player["seat"]] = [self.slot_card(slot) for slot in player["slots"]]
        self.selected = None
        self.pending = False
        self.notice = ""
        self.page = min(self.page, self.max_page)

    def slot_card(self, slot):
        if slot is None:
            return None
        card = copy(self.session.catalogue.cards[slot["id"]])
        card.hp, card.shield = slot["hp"], slot["shield"]
        return card

    @property
    def max_page(self):
        return max(0, (len(self.state["hand"]) - 1) // CARDS_PER_PAGE)

    @property
    def can_act(self):
        return self.state["result"] is None and self.state["active"] == self.seat and not self.pending

    @property
    def valid_targets(self):
        if self.selected is None or not self.can_act:
            return set()
        return {tuple(target) for target in self.state["targets"][self.selected]}

    def hand_positions(self):
        start = self.page * CARDS_PER_PAGE
        cards = self.state["hand"][start:start + CARDS_PER_PAGE]
        height = round(HAND_CARD_WIDTH * CARD_HEIGHT_RATIO)
        step = HAND_CARD_WIDTH + HAND_CARD_GAP
        left = (WIDTH - len(cards) * step + HAND_CARD_GAP) // 2
        for offset, card_id in enumerate(cards):
            rect = pygame.Rect(left + offset * step, HEIGHT - HAND_BOTTOM_MARGIN - height, HAND_CARD_WIDTH, height)
            yield start + offset, self.session.catalogue.cards[card_id], rect

    def plaque_rect(self, seat):
        slot = next(rect for player, _, _, rect in self.terrain_ui.positions((WIDTH, HEIGHT), self.seat) if player == seat)
        if seat == self.opponent:
            rect = pygame.Rect(0, 0, 384, 88)
            rect.midbottom = (WIDTH // 2, slot.top)
        else:
            rect = pygame.Rect(0, 0, 310, 58)
            rect.midtop = (WIDTH // 2, slot.bottom)
        return rect

    def submit(self, kind, **data):
        if self.can_act:
            self.pending = True
            self.session.submit({"type": kind, "revision": self.state["revision"], **data})

    def change_page(self, offset):
        self.page = max(0, min(self.max_page, self.page + offset))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.leave()
        elif event.type == pygame.MOUSEWHEEL:
            self.change_page(-event.y)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            position = self.menu.to_canvas_position(event.pos)
            if self.back_rect.collidepoint(position):
                self.leave()
            elif self.pass_rect.collidepoint(position):
                self.submit("pass")
            elif self.draw_rect.collidepoint(position) and self.state["can_draw"]:
                self.submit("draw")
            elif self.prev_rect.collidepoint(position):
                self.change_page(-1)
            elif self.next_rect.collidepoint(position):
                self.change_page(1)
            elif self.can_act:
                self.select(position)

    def select(self, position):
        for index, _, rect in self.hand_positions():
            if rect.collidepoint(position):
                self.selected = None if self.selected == index else index
                self.notice = "" if self.selected is None or self.valid_targets else "Cette carte ne peut pas être jouée."
                return
        if (self.opponent, None) in self.valid_targets and self.plaque_rect(self.opponent).collidepoint(position):
            self.submit("play", card=self.selected, target=self.opponent, slot=None)
            return
        for seat, index, _, rect in self.terrain_ui.positions((WIDTH, HEIGHT), self.seat):
            if (seat, index) in self.valid_targets and rect.collidepoint(position):
                self.submit("play", card=self.selected, target=seat, slot=index)
                return

    def update(self, dt):
        self.pointer = self.menu.to_canvas_position(pygame.mouse.get_pos())
        for event in self.session.poll():
            if event["type"] == "closed":
                if self.state["result"] is None:
                    self.leave(event["value"])
                    return
            elif event["type"] == "state":
                self.set_state(event["value"])
            elif event["type"] == "error":
                self.pending = False
                self.notice = event["value"]

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
            pygame.draw.line(shade, (*SHADOW, round(max(26, top_shade, bottom_shade))), (0, y), (WIDTH - 1, y))
        background.blit(shade, (0, 0))
        return background

    def button(self, surface, rect, label, enabled=True):
        color = METAL if not enabled else (85, 62, 35) if rect.collidepoint(self.pointer) else (51, 49, 39)
        pygame.draw.rect(surface, color, rect, border_radius=10)
        pygame.draw.rect(surface, GOLD if enabled else METAL_EDGE, rect, width=2, border_radius=10)
        self.menu.draw_centered(surface, label, self.small_font, INK if enabled else (151, 153, 148), rect.center)

    def status(self):
        result = self.state["result"]
        if result is not None:
            return "Match nul" if result == "draw" else "Victoire" if result == self.seat else "Défaite"
        turn = "Votre tour" if self.state["active"] == self.seat else "Tour adverse"
        return f"{turn}  ·  Tour {self.state['turn']}"

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        self.button(surface, self.back_rect, "Menu")
        self.button(surface, self.pass_rect, "Passer", self.can_act)
        self.terrain_ui.draw(surface, self.seat, fill_background=False)
        targets = self.valid_targets
        for seat, index, _, rect in self.terrain_ui.positions((WIDTH, HEIGHT), self.seat):
            if (seat, index) in targets:
                pygame.draw.rect(surface, GOLD, rect, width=3, border_radius=8)

        label = self.menu.draw_centered
        for player in self.state["players"]:
            seat = player["seat"]
            own = seat == self.seat
            rect = self.plaque_rect(seat)
            surface.blit(pygame.transform.smoothscale(self.plaque, rect.size), rect)
            if (seat, None) in targets:
                pygame.draw.rect(surface, GOLD, rect, width=3, border_radius=8)
            name = "Vous" if own else "Bot" if self.session.mode == "solo" else "Adversaire"
            title = f"{name}  ·  {player['hp']} PV"
            label(surface, title, self.button_font, HEALTH_COLOR, (rect.centerx, rect.centery - (9 if not own else 0)))
            if not own:
                label(surface, f"{player['hand_count']} en main  ·  {player['deck_count']} en pioche",
                      self.small_font, INK, (rect.centerx, rect.centery + 17))

        label(surface, self.status(), self.button_font, GOLD, (WIDTH // 2, 514))
        hint = self.notice or ("Choisissez une cible" if targets else "")
        label(surface, hint, self.small_font, INK, (WIDTH // 2, 552))

        for index, card, rect in self.hand_positions():
            self.card_view.draw(surface, rect, card)
            if index == self.selected:
                pygame.draw.rect(surface, GOLD, rect, width=3, border_radius=8)
        if self.max_page:
            self.button(surface, self.prev_rect, "Précédentes", self.page > 0)
            self.button(surface, self.next_rect, "Suivantes", self.page < self.max_page)
            label(surface, f"{self.page + 1} / {self.max_page + 1}", self.small_font, INK, (WIDTH // 2, 1150))

        own = self.state["players"][self.seat - 1]
        maximum = self.state["max_energy"]
        cost = self.state["draw_cost"]
        self.button(surface, self.energy_rect, f"Énergie  {own['energy']} / {maximum}")
        self.button(surface, self.draw_rect, f"Piocher · {cost} énergie", self.state["can_draw"] and self.can_act)
