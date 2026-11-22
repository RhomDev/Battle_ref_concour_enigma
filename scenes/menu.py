from bisect import bisect_right
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
GREEN_ACCENT = (46, 204, 113)


class MenuScene:
    _intro_already_played = False

    def __init__(self, game):
        self.game = game
        self.background = self.make_background()
        self.font_title = pygame.font.SysFont("arial", 88, bold=True)
        self.font_play = pygame.font.SysFont("arial", 43, bold=True)
        self.font_button = pygame.font.SysFont("arial", 30, bold=True)
        self.font_small = pygame.font.SysFont("arial", 24)
        self.font_intro = pygame.font.SysFont("arial", 36, bold=True)

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

        # Gestion de l'apparition de The Mask lors de la première entrée dans le menu
        self.intro_active = False
        self.intro_channel = None
        self.intro_frames = []
        self.intro_times = []
        self.intro_started_at = None
        self.intro_duration_ms = 7900

        if not MenuScene._intro_already_played:
            MenuScene._intro_already_played = True
            self.start_the_mask_intro()

    def start_the_mask_intro(self):
        # 1. Jouer le son
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            sound_path = ROOT / "asset/sound/the_mask_splendide.mp3"
            if sound_path.exists():
                sound = pygame.mixer.Sound(str(sound_path))
                self.intro_channel = sound.play()
        except Exception:
            self.intro_channel = None

        # 2. Charger les frames de l'animation vidéo/gif de The Mask
        try:
            from PIL import Image, ImageSequence
            gif_path = ROOT / "asset/gif/the_mask_splendide.gif"
            if gif_path.exists():
                total = 0
                with Image.open(gif_path) as image:
                    for frame in ImageSequence.Iterator(image):
                        rgba = frame.convert("RGBA")
                        surface = pygame.image.frombytes(rgba.tobytes(), rgba.size, "RGBA")
                        # Redimensionnement adapté au popup
                        scaled = pygame.transform.smoothscale(surface, (540, 306))
                        self.intro_frames.append(scaled)
                        total += max(20, frame.info.get("duration", 100))
                        self.intro_times.append(total)
                        if total >= self.intro_duration_ms:
                            break
        except Exception:
            self.intro_frames = []
            self.intro_times = []

        if self.intro_channel is not None or self.intro_frames:
            self.intro_active = True
            self.intro_started_at = pygame.time.get_ticks()

    def dismiss_intro(self):
        if not self.intro_active:
            return
        self.intro_active = False
        if self.intro_channel is not None:
            try:
                self.intro_channel.stop()
            except Exception:
                pass
            self.intro_channel = None
        self.intro_frames = []
        self.intro_times = []
        self.intro_started_at = None

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
        # Si l'intro The Mask est affichée, n'importe quelle interaction la passe
        if self.intro_active:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.dismiss_intro()
                return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = self.to_canvas_position(event.pos)
            if self.play_rect.collidepoint(mouse):
                from scenes.mode_select import ModeSelectScene
                if self.game:
                    self.game.change_scene(ModeSelectScene(self))
            elif self.characters_rect.collidepoint(mouse):
                if self.game:
                    self.game.change_scene(MediaCollectionScene(self, "character"))
            elif self.references_rect.collidepoint(mouse):
                if self.game:
                    self.game.change_scene(MediaCollectionScene(self, "ref"))
            elif self.quit_rect.collidepoint(mouse):
                if self.game:
                    self.game.running = False

    def update(self, dt):
        self.mouse_pos = self.to_canvas_position(pygame.mouse.get_pos())

        # Mise à jour de l'intro
        if self.intro_active and self.intro_started_at is not None:
            elapsed = pygame.time.get_ticks() - self.intro_started_at
            sound_playing = self.intro_channel is not None and self.intro_channel.get_busy()
            if elapsed >= self.intro_duration_ms and not sound_playing:
                self.dismiss_intro()

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

    def draw_the_mask_intro(self, surface):
        # Voile sombre
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 18, 220))
        surface.blit(overlay, (0, 0))

        # Cadre pop-up
        popup_width = min(620, WIDTH - 40)
        popup_height = 490
        popup_rect = pygame.Rect(
            (WIDTH - popup_width) // 2,
            (HEIGHT - popup_height) // 2,
            popup_width,
            popup_height,
        )
        pygame.draw.rect(surface, PANEL, popup_rect, border_radius=18)
        pygame.draw.rect(surface, GOLD, popup_rect, width=3, border_radius=18)

        # En-tête
        title = self.font_intro.render("SSSPLENDIDE !", True, GREEN_ACCENT)
        surface.blit(title, title.get_rect(center=(WIDTH // 2, popup_rect.top + 38)))

        sub = self.font_small.render("The Mask débarque dans l'arène !", True, INK)
        surface.blit(sub, sub.get_rect(center=(WIDTH // 2, popup_rect.top + 76)))

        # Image ou frame animée
        video_area = pygame.Rect(popup_rect.left + 40, popup_rect.top + 106, popup_width - 80, 306)
        pygame.draw.rect(surface, (15, 18, 26), video_area, border_radius=10)

        if self.intro_frames and self.intro_started_at is not None:
            elapsed = pygame.time.get_ticks() - self.intro_started_at
            frame_idx = bisect_right(self.intro_times, elapsed % self.intro_times[-1])
            frame_surf = self.intro_frames[frame_idx]
            surface.blit(frame_surf, frame_surf.get_rect(center=video_area.center))

        pygame.draw.rect(surface, BORDER, video_area, width=1, border_radius=10)

        # Footer / skip hint
        skip_hint = self.font_small.render("Cliquez ou appuyez sur une touche pour passer", True, MUTED)
        surface.blit(skip_hint, skip_hint.get_rect(center=(WIDTH // 2, popup_rect.bottom - 26)))

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

        # Si l'intro est active, l'afficher par-dessus le menu
        if self.intro_active:
            self.draw_the_mask_intro(surface)
