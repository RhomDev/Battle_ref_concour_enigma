import pygame

from config import HEIGHT, WIDTH
from core.asset_manager import ROOT
from scenes.media_collection import GOLD, INK


BACKGROUND = (20, 24, 36)
PANEL = (29, 35, 51)
PANEL_HOVER = (39, 48, 65)
BORDER = (59, 67, 83)
MUTED = (166, 173, 189)


class ModeSelectScene:
    def __init__(self, menu):
        self.menu = menu
        self.game = menu.game
        self.background = menu.background
        self.font_title = pygame.font.SysFont("arial", 56, bold=True)
        self.font_sub = pygame.font.SysFont("arial", 22)
        self.font_button = pygame.font.SysFont("arial", 32, bold=True)
        self.font_desc = pygame.font.SysFont("arial", 20)
        self.font_back = pygame.font.SysFont("arial", 24)

        margin = 40
        btn_width = WIDTH - 2 * margin
        btn_height = 110
        start_y = 380
        gap = 26

        self.solo_rect = pygame.Rect(margin, start_y, btn_width, btn_height)
        self.host_rect = pygame.Rect(margin, start_y + btn_height + gap, btn_width, btn_height)
        self.join_rect = pygame.Rect(margin, start_y + 2 * (btn_height + gap), btn_width, btn_height)

        self.back_rect = pygame.Rect(0, 0, 180, 60)
        self.back_rect.midbottom = (WIDTH // 2, HEIGHT - 50)
        self.mouse_pos = (-1, -1)

    def to_canvas_position(self, pos):
        return self.menu.to_canvas_position(pos)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.change_scene(self.menu)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.to_canvas_position(event.pos)
            if self.solo_rect.collidepoint(pos):
                from scenes.battle_scene import BattleScene
                self.game.change_scene(BattleScene(self.menu, mode="solo"))
            elif self.host_rect.collidepoint(pos):
                from scenes.host_scene import HostScene
                self.game.change_scene(HostScene(self.menu))
            elif self.join_rect.collidepoint(pos):
                from scenes.join_scene import JoinScene
                self.game.change_scene(JoinScene(self.menu))
            elif self.back_rect.collidepoint(pos):
                self.game.change_scene(self.menu)

    def update(self, dt):
        self.mouse_pos = self.to_canvas_position(pygame.mouse.get_pos())

    def draw_card_button(self, surface, rect, title, description, icon_type="solo"):
        hovered = rect.collidepoint(self.mouse_pos)
        pygame.draw.rect(surface, PANEL_HOVER if hovered else PANEL, rect, border_radius=14)
        pygame.draw.rect(surface, GOLD if hovered else BORDER, rect, width=2, border_radius=14)

        # Icône décorative
        icon_rect = pygame.Rect(rect.left + 24, rect.centery - 24, 48, 48)
        pygame.draw.rect(surface, (18, 22, 33), icon_rect, border_radius=8)
        pygame.draw.rect(surface, GOLD if hovered else BORDER, icon_rect, width=1, border_radius=8)

        cx, cy = icon_rect.center
        if icon_type == "solo":
            pygame.draw.circle(surface, GOLD, (cx, cy - 6), 9, width=2)
            pygame.draw.arc(surface, GOLD, pygame.Rect(cx - 14, cy + 2, 28, 22), 3.14, 0, 2)
        elif icon_type == "host":
            # Icône Antenne / Wi-Fi
            pygame.draw.circle(surface, GOLD, (cx, cy + 10), 4)
            pygame.draw.arc(surface, GOLD, pygame.Rect(cx - 12, cy - 2, 24, 24), 0.7, 2.4, 2)
            pygame.draw.arc(surface, GOLD, pygame.Rect(cx - 20, cy - 10, 40, 40), 0.7, 2.4, 2)
        elif icon_type == "join":
            # Icône Connexion / Flèche vers le centre
            pygame.draw.circle(surface, GOLD, (cx - 8, cy), 6, width=2)
            pygame.draw.circle(surface, GOLD, (cx + 8, cy), 6, width=2)
            pygame.draw.line(surface, GOLD, (cx - 2, cy), (cx + 2, cy), 2)

        # Textes
        t_surf = self.font_button.render(title, True, INK)
        surface.blit(t_surf, (rect.left + 88, rect.top + 22))

        d_surf = self.font_desc.render(description, True, MUTED)
        surface.blit(d_surf, (rect.left + 88, rect.top + 64))

        # Chevron droite
        x, y = rect.right - 28, rect.centery
        chevron = [(x - 6, y - 8), (x + 2, y), (x - 6, y + 8)]
        pygame.draw.lines(surface, GOLD if hovered else MUTED, False, chevron, 2)

    def draw(self, surface):
        surface.blit(self.background, (0, 0))

        center_x = WIDTH // 2
        title_surf = self.font_title.render("MODE DE JEU", True, INK)
        surface.blit(title_surf, title_surf.get_rect(center=(center_x, 180)))

        sub_surf = self.font_sub.render("Multijoueur en réseau local ou partie solo", True, GOLD)
        surface.blit(sub_surf, sub_surf.get_rect(center=(center_x, 235)))

        pygame.draw.line(surface, BORDER, (60, 280), (WIDTH - 60, 280), 2)

        self.draw_card_button(surface, self.solo_rect, "Partie Solo", "Jouez contre l'intelligence artificielle locale", "solo")
        self.draw_card_button(surface, self.host_rect, "Créer une partie", "Hébergez via le point d'accès Wi-Fi de votre téléphone", "host")
        self.draw_card_button(surface, self.join_rect, "Rejoindre une partie", "Connectez-vous à la partie hébergée par un ami", "join")

        back_hovered = self.back_rect.collidepoint(self.mouse_pos)
        if back_hovered:
            pygame.draw.rect(surface, PANEL_HOVER, self.back_rect, border_radius=12)
        b_surf = self.font_back.render("Retour", True, INK if back_hovered else MUTED)
        surface.blit(b_surf, b_surf.get_rect(center=self.back_rect.center))
