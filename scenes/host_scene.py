import math
import pygame
import time

from config import HEIGHT, WIDTH
from core.network import DEFAULT_TCP_PORT, DiscoveryBeacon, GameServer, get_local_ip
from scenes.media_collection import GOLD, INK


BACKGROUND = (20, 24, 36)
PANEL = (29, 35, 51)
PANEL_HOVER = (39, 48, 65)
BORDER = (59, 67, 83)
MUTED = (166, 173, 189)
GREEN = (72, 187, 120)


class HostScene:
    def __init__(self, menu):
        self.menu = menu
        self.game = menu.game
        self.background = menu.background

        self.font_title = pygame.font.SysFont("arial", 48, bold=True)
        self.font_sub = pygame.font.SysFont("arial", 22)
        self.font_info = pygame.font.SysFont("arial", 26, bold=True)
        self.font_ip = pygame.font.SysFont("arial", 44, bold=True)
        self.font_text = pygame.font.SysFont("arial", 20)
        self.font_btn = pygame.font.SysFont("arial", 26, bold=True)

        self.local_ip = get_local_ip()
        self.port = DEFAULT_TCP_PORT

        # Démarrage du serveur et de la balise UDP
        self.server = GameServer(host_ip="0.0.0.0", port=self.port, host_name="Joueur 1 (Hôte)")
        self.server.start()

        self.beacon = DiscoveryBeacon(host_name="Partie de Joueur 1", tcp_port=self.port)
        self.beacon.start()

        self.cancel_rect = pygame.Rect(0, 0, 220, 60)
        self.cancel_rect.midbottom = (WIDTH // 2, HEIGHT - 60)
        self.mouse_pos = (-1, -1)

        self.animation_timer = 0
        self.player_joined = False
        self.join_timestamp = 0

    def to_canvas_position(self, pos):
        return self.menu.to_canvas_position(pos)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.cleanup()
            from scenes.mode_select import ModeSelectScene
            self.game.change_scene(ModeSelectScene(self.menu))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.to_canvas_position(event.pos)
            if self.cancel_rect.collidepoint(pos):
                self.cleanup()
                from scenes.mode_select import ModeSelectScene
                self.game.change_scene(ModeSelectScene(self.menu))

    def cleanup(self):
        if self.beacon:
            self.beacon.stop()
            self.beacon = None
        if self.server:
            self.server.stop()
            self.server = None

    def update(self, dt):
        self.mouse_pos = self.to_canvas_position(pygame.mouse.get_pos())
        self.animation_timer += dt

        if self.server:
            events = self.server.poll_events()
            for ev in events:
                if ev.get("type") == "player_joined":
                    self.player_joined = True
                    self.join_timestamp = time.time()

        if self.player_joined and time.time() - self.join_timestamp > 0.6:
            # Arrêt de la balise broadcast une fois le joueur connecté
            if self.beacon:
                self.beacon.stop()
                self.beacon = None
            from scenes.battle_scene import BattleScene
            self.game.change_scene(BattleScene(self.menu, mode="host", server=self.server))

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        cx = WIDTH // 2

        # Titre
        t_surf = self.font_title.render("CRÉER UNE PARTIE", True, INK)
        surface.blit(t_surf, t_surf.get_rect(center=(cx, 140)))

        sub_surf = self.font_sub.render("Serveur local prêt", True, GOLD)
        surface.blit(sub_surf, sub_surf.get_rect(center=(cx, 195)))

        # Panneau Informations IP
        info_rect = pygame.Rect(40, 240, WIDTH - 80, 240)
        pygame.draw.rect(surface, PANEL, info_rect, border_radius=16)
        pygame.draw.rect(surface, BORDER, info_rect, width=2, border_radius=16)

        lbl = self.font_sub.render("VOTRE ADRESSE IP LOCALE :", True, MUTED)
        surface.blit(lbl, lbl.get_rect(center=(cx, info_rect.top + 40)))

        ip_surf = self.font_ip.render(self.local_ip, True, GOLD)
        surface.blit(ip_surf, ip_surf.get_rect(center=(cx, info_rect.top + 95)))

        port_str = f"Port réseau : {self.port}"
        port_surf = self.font_text.render(port_str, True, MUTED)
        surface.blit(port_surf, port_surf.get_rect(center=(cx, info_rect.top + 145)))

        hint = self.font_text.render("L'autre joueur peut se connecter à cette IP ou utiliser la détection auto.", True, INK)
        surface.blit(hint, hint.get_rect(center=(cx, info_rect.top + 195)))

        # Instructions Android Hotspot
        inst_rect = pygame.Rect(40, 510, WIDTH - 80, 160)
        pygame.draw.rect(surface, (24, 30, 44), inst_rect, border_radius=14)
        pygame.draw.rect(surface, BORDER, inst_rect, width=1, border_radius=14)

        lines = [
            "Conseil pour jouer sans box Internet :",
            "1. Activez le « Partage de connexion » (Point d'accès Wi-Fi)",
            "2. Faites connecter le 2nd téléphone au Wi-Fi du premier",
            "3. L'adresse standard du point d'accès Android est 192.168.43.1",
        ]
        y_off = inst_rect.top + 24
        for i, line in enumerate(lines):
            col = GOLD if i == 0 else INK
            f = self.font_info if i == 0 else self.font_text
            l_surf = f.render(line, True, col)
            surface.blit(l_surf, (inst_rect.left + 24, y_off))
            y_off += 30

        # Animation d'attente
        radar_y = 780
        if not self.player_joined:
            pulse = (math.sin(self.animation_timer * 3) + 1) / 2
            r1 = int(24 + 16 * pulse)
            r2 = int(48 + 20 * pulse)
            pygame.draw.circle(surface, (45, 60, 85), (cx, radar_y), r2, width=1)
            pygame.draw.circle(surface, GOLD, (cx, radar_y), r1, width=2)
            pygame.draw.circle(surface, GOLD, (cx, radar_y), 8)

            status_str = "En attente du joueur 2..."
            col_status = INK
        else:
            pygame.draw.circle(surface, GREEN, (cx, radar_y), 32)
            pygame.draw.circle(surface, INK, (cx, radar_y), 12)
            status_str = "Joueur 2 connecté ! Lancement..."
            col_status = GREEN

        st_surf = self.font_info.render(status_str, True, col_status)
        surface.blit(st_surf, st_surf.get_rect(center=(cx, radar_y + 80)))

        # Bouton Annuler
        hovered = self.cancel_rect.collidepoint(self.mouse_pos)
        pygame.draw.rect(surface, PANEL_HOVER if hovered else PANEL, self.cancel_rect, border_radius=12)
        pygame.draw.rect(surface, GOLD if hovered else BORDER, self.cancel_rect, width=2, border_radius=12)
        c_surf = self.font_btn.render("Annuler", True, INK if hovered else MUTED)
        surface.blit(c_surf, c_surf.get_rect(center=self.cancel_rect.center))
