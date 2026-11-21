import pygame

from config import HEIGHT, WIDTH
from core.asset_manager import ROOT
from scenes.battle_scene import BattleScene
from scenes.media_collection import GOLD, INK, MediaCollectionScene


BACKGROUND = (20, 24, 36)
PANEL = (29, 35, 51)
PANEL_HOVER = (39, 48, 65)
BORDER = (59, 67, 83)
MUTED = (166, 173, 189)


class MenuScene:
    def __init__(self, game):
        self.game = game
        self.background = self.make_background()
        self.font_title = pygame.font.SysFont("arial", 88, bold=True)
        self.font_play = pygame.font.SysFont("arial", 43, bold=True)
        self.font_button = pygame.font.SysFont("arial", 30, bold=True)
        self.font_small = pygame.font.SysFont("arial", 24)

        margin = 36
        content_width = WIDTH - 2 * margin
        column_width = (content_width - 16) // 2
        self.play_rect = pygame.Rect(margin, 694, content_width, 132)
        self.characters_rect = pygame.Rect(margin, 922, column_width, 144)
        self.references_rect = self.characters_rect.move(column_width + 16, 0)
        self.quit_rect = pygame.Rect(0, 0, 180, 64)
        self.quit_rect.midbottom = (WIDTH // 2, HEIGHT - 48)
        self.mouse_pos = (-1, -1)
        self.battle_scene = None

    @staticmethod
    def make_background():
        background = pygame.Surface((WIDTH, HEIGHT))
        background.fill(BACKGROUND)
        try:
            arena = pygame.image.load(ROOT / "asset/board/theatre-des-echos.webp")
        except (OSError, pygame.error):
            return background

        hero_height = 724
        scale = max(WIDTH / arena.get_width(), hero_height / arena.get_height())
        size = (round(arena.get_width() * scale), round(arena.get_height() * scale))
        arena = pygame.transform.smoothscale(arena, size)
        background.blit(arena, ((WIDTH - size[0]) // 2, (hero_height - size[1]) // 2))

        shade = pygame.Surface((WIDTH, hero_height), pygame.SRCALPHA)
        for y in range(hero_height):
            title_shade = 244 * (1 - min(1, y / 433))
            bottom_shade = 255 * max(0, (y - 436) / (hero_height - 1 - 436))
            alpha = round(max(title_shade, bottom_shade))
            pygame.draw.line(shade, (*BACKGROUND, alpha), (0, y), (WIDTH - 1, y))
        background.blit(shade, (0, 0))
        return background

    def to_canvas_position(self, pos):
        window_w, window_h = self.game.screen.get_size()
        scale = min(window_w / WIDTH, window_h / HEIGHT)
        canvas_w = max(1, int(WIDTH * scale))
        canvas_h = max(1, int(HEIGHT * scale))
        offset_x = (window_w - canvas_w) // 2
        offset_y = (window_h - canvas_h) // 2
        return (
            (pos[0] - offset_x) * WIDTH // canvas_w,
            (pos[1] - offset_y) * HEIGHT // canvas_h,
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = self.to_canvas_position(event.pos)
            if self.play_rect.collidepoint(mouse):
                if self.battle_scene is None:
                    self.battle_scene = BattleScene(self)
                self.game.change_scene(self.battle_scene)
            elif self.characters_rect.collidepoint(mouse):
                self.game.change_scene(MediaCollectionScene(self, "character"))
            elif self.references_rect.collidepoint(mouse):
                self.game.change_scene(MediaCollectionScene(self, "ref"))
            elif self.quit_rect.collidepoint(mouse):
                self.game.running = False

    def update(self, dt):
        self.mouse_pos = self.to_canvas_position(pygame.mouse.get_pos())

    @staticmethod
    def draw_centered(surface, text, font, color, center):
        label = font.render(text, True, color)
        surface.blit(label, label.get_rect(center=center))

    def draw_collection_button(self, surface, rect, label):
        hovered = rect.collidepoint(self.mouse_pos)
        pygame.draw.rect(surface, PANEL_HOVER if hovered else PANEL, rect, border_radius=14)
        pygame.draw.rect(surface, GOLD if hovered else BORDER, rect, width=2, border_radius=14)

        icon = pygame.Rect(rect.left + 27, rect.top + 22, 23, 33)
        if rect == self.characters_rect:
            for offset in (12, 6):
                pygame.draw.rect(surface, BORDER, icon.move(offset, 0), width=2, border_radius=4)
        pygame.draw.rect(surface, PANEL, icon, border_radius=4)
        pygame.draw.rect(surface, GOLD, icon, width=2, border_radius=4)
        if rect == self.references_rect:
            x, y = icon.center
            bolt = [(x + 2, y - 9), (x - 4, y), (x + 4, y), (x - 2, y + 9)]
            pygame.draw.lines(surface, GOLD, False, bolt, 2)

        title = self.font_button.render(label, True, INK)
        surface.blit(title, title.get_rect(midleft=(rect.left + 26, rect.top + 97)))
        x, y = rect.right - 31, rect.top + 97
        chevron = [(x - 4, y - 6), (x + 2, y), (x - 4, y + 6)]
        pygame.draw.lines(surface, GOLD if hovered else MUTED, False, chevron, 2)

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        center_x = WIDTH // 2
        self.draw_centered(surface, "BATTLE REF", self.font_title, INK, (center_x, 145))
        subtitle = self.font_button.render("ARENA", True, GOLD)
        subtitle_rect = subtitle.get_rect(center=(center_x, 216))
        surface.blit(subtitle, subtitle_rect)
        left_line = subtitle_rect.left - 16
        right_line = subtitle_rect.right + 16
        pygame.draw.line(surface, GOLD, (left_line - 49, 216), (left_line, 216), 2)
        pygame.draw.line(surface, GOLD, (right_line, 216), (right_line + 49, 216), 2)

        play_hovered = self.play_rect.collidepoint(self.mouse_pos)
        pygame.draw.rect(surface, PANEL_HOVER if play_hovered else PANEL, self.play_rect, border_radius=14)
        pygame.draw.rect(surface, GOLD, self.play_rect, width=2, border_radius=14)
        self.draw_centered(surface, "Jouer", self.font_play, INK, self.play_rect.center)

        heading = self.font_button.render("Collection", True, GOLD)
        heading_rect = heading.get_rect(midleft=(self.characters_rect.left, 879))
        surface.blit(heading, heading_rect)
        pygame.draw.line(surface, BORDER, (heading_rect.right + 20, 879), (self.references_rect.right, 879), 2)
        self.draw_collection_button(surface, self.characters_rect, "Personnages")
        self.draw_collection_button(surface, self.references_rect, "Références")

        quit_hovered = self.quit_rect.collidepoint(self.mouse_pos)
        if quit_hovered:
            pygame.draw.rect(surface, PANEL_HOVER, self.quit_rect, border_radius=12)
        self.draw_centered(
            surface, "Quitter", self.font_small, INK if quit_hovered else MUTED, self.quit_rect.center
        )
