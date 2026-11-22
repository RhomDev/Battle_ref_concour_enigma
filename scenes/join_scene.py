import pygame
import threading
import time

from config import HEIGHT, WIDTH
from core.network import DEFAULT_TCP_PORT, DiscoveryListener, GameClient, HOTSPOT_DEFAULT_IP
from scenes.media_collection import GOLD, INK


BACKGROUND = (20, 24, 36)
PANEL = (29, 35, 51)
PANEL_HOVER = (39, 48, 65)
BORDER = (59, 67, 83)
MUTED = (166, 173, 189)
GREEN = (72, 187, 120)
RED = (229, 62, 62)


class JoinScene:
    def __init__(self, menu):
        self.menu = menu
        self.game = menu.game
        self.background = menu.background

        self.font_title = pygame.font.SysFont("arial", 46, bold=True)
        self.font_sub = pygame.font.SysFont("arial", 22)
        self.font_section = pygame.font.SysFont("arial", 22, bold=True)
        self.font_ip = pygame.font.SysFont("arial", 32, bold=True)
        self.font_btn = pygame.font.SysFont("arial", 24, bold=True)
        self.font_keypad = pygame.font.SysFont("arial", 26, bold=True)
        self.font_small = pygame.font.SysFont("arial", 18)

        # Écouteur UDP pour découverte automatique
        self.listener = DiscoveryListener()
        self.listener.start()

        self.client = None
        self.connecting = False
        self.status_message = ""
        self.status_color = MUTED

        # Saisie d'IP manuelle
        self.ip_input = HOTSPOT_DEFAULT_IP
        self.port = DEFAULT_TCP_PORT

        # Clavier virtuel pour Android tactile
        # Grille 4 lignes x 3 colonnes :
        # 1  2  3
        # 4  5  6
        # 7  8  9
        # .  0  ⌫
        self.keypad_rects = {}
        pad_keys = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            [".", "0", "Effacer"],
        ]
        start_x = 70
        start_y = 660
        btn_w = (WIDTH - 140 - 20) // 3
        btn_h = 56
        gap = 10

        for r, row in enumerate(pad_keys):
            for c, key in enumerate(row):
                rx = start_x + c * (btn_w + gap)
                ry = start_y + r * (btn_h + gap)
                self.keypad_rects[key] = pygame.Rect(rx, ry, btn_w, btn_h)

        # Boutons d'action
        self.quick_hotspot_rect = pygame.Rect(60, 480, WIDTH - 120, 52)
        self.connect_rect = pygame.Rect(60, 940, WIDTH - 120, 64)
        self.back_rect = pygame.Rect(0, 0, 180, 56)
        self.back_rect.midbottom = (WIDTH // 2, HEIGHT - 40)

        self.mouse_pos = (-1, -1)

    def to_canvas_position(self, pos):
        return self.menu.to_canvas_position(pos)

    def cleanup(self):
        if self.listener:
            self.listener.stop()
            self.listener = None

    def start_connection(self, host_ip, port=DEFAULT_TCP_PORT):
        if self.connecting:
            return
        self.connecting = True
        self.status_message = f"Connexion à {host_ip}:{port}..."
        self.status_color = GOLD

        def _connect_thread():
            client = GameClient(player_name="Joueur 2")
            ok, msg = client.connect(host_ip, port=port, timeout=3.5)
            if ok:
                self.client = client
                self.status_message = "Connecté ! Chargement..."
                self.status_color = GREEN
            else:
                self.connecting = False
                self.status_message = msg
                self.status_color = RED

        threading.Thread(target=_connect_thread, daemon=True).start()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.cleanup()
                from scenes.mode_select import ModeSelectScene
                self.game.change_scene(ModeSelectScene(self.menu))
            elif event.key == pygame.K_BACKSPACE:
                if len(self.ip_input) > 0:
                    self.ip_input = self.ip_input[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.start_connection(self.ip_input.strip())
            elif event.unicode in "0123456789.":
                if len(self.ip_input) < 15:
                    self.ip_input += event.unicode

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.to_canvas_position(event.pos)

            if self.back_rect.collidepoint(pos):
                self.cleanup()
                from scenes.mode_select import ModeSelectScene
                self.game.change_scene(ModeSelectScene(self.menu))

            elif self.quick_hotspot_rect.collidepoint(pos):
                self.ip_input = HOTSPOT_DEFAULT_IP
                self.start_connection(HOTSPOT_DEFAULT_IP)

            elif self.connect_rect.collidepoint(pos):
                if self.ip_input.strip():
                    self.start_connection(self.ip_input.strip())

            # Clic sur le pavé tactile
            for key, krect in self.keypad_rects.items():
                if krect.collidepoint(pos):
                    if key == "Effacer":
                        if len(self.ip_input) > 0:
                            self.ip_input = self.ip_input[:-1]
                    elif len(self.ip_input) < 15:
                        self.ip_input += key

            # Clic sur un serveur découvert
            servers = self.listener.get_discovered_servers() if self.listener else []
            for i, srv in enumerate(servers[:3]):
                srv_rect = pygame.Rect(60, 260 + i * 62, WIDTH - 120, 52)
                if srv_rect.collidepoint(pos):
                    self.ip_input = srv["ip"]
                    self.start_connection(srv["ip"], srv.get("port", DEFAULT_TCP_PORT))

    def update(self, dt):
        self.mouse_pos = self.to_canvas_position(pygame.mouse.get_pos())

        if self.client and self.client.connected:
            self.cleanup()
            from scenes.battle_scene import BattleScene
            self.game.change_scene(BattleScene(self.menu, mode="client", client=self.client))

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        cx = WIDTH // 2

        # Titre
        t_surf = self.font_title.render("REJOINDRE UNE PARTIE", True, INK)
        surface.blit(t_surf, t_surf.get_rect(center=(cx, 90)))

        # Section 1 : Découverte automatique
        sec1 = self.font_section.render("1. PARTIES DÉCOUVERTES SUR LE RÉSEAU", True, GOLD)
        surface.blit(sec1, (60, 140))

        servers = self.listener.get_discovered_servers() if self.listener else []
        if servers:
            for i, srv in enumerate(servers[:3]):
                srv_rect = pygame.Rect(60, 180 + i * 62, WIDTH - 120, 52)
                hovered = srv_rect.collidepoint(self.mouse_pos)
                pygame.draw.rect(surface, PANEL_HOVER if hovered else PANEL, srv_rect, border_radius=10)
                pygame.draw.rect(surface, GREEN if hovered else BORDER, srv_rect, width=2, border_radius=10)

                name_surf = self.font_btn.render(srv["name"], True, INK)
                surface.blit(name_surf, (srv_rect.left + 16, srv_rect.top + 12))

                ip_txt = f"{srv['ip']}:{srv['port']}"
                ip_s = self.font_small.render(ip_txt, True, MUTED)
                surface.blit(ip_s, ip_s.get_rect(midright=(srv_rect.right - 16, srv_rect.centery)))
        else:
            none_rect = pygame.Rect(60, 180, WIDTH - 120, 48)
            pygame.draw.rect(surface, (18, 22, 33), none_rect, border_radius=10)
            none_txt = self.font_small.render("Recherche en cours... (activez le Wi-Fi/Hotspot)", True, MUTED)
            surface.blit(none_txt, none_txt.get_rect(center=none_rect.center))

        pygame.draw.line(surface, BORDER, (60, 370), (WIDTH - 60, 370), 1)

        # Section 2 : Connexion directe / IP
        sec2 = self.font_section.render("2. CONNEXION MANUELLE OU POINT D'ACCÈS", True, GOLD)
        surface.blit(sec2, (60, 395))

        # Boîte de saisie IP
        input_rect = pygame.Rect(60, 435, WIDTH - 120, 58)
        pygame.draw.rect(surface, (15, 18, 28), input_rect, border_radius=10)
        pygame.draw.rect(surface, GOLD, input_rect, width=2, border_radius=10)

        ip_render = self.ip_input if self.ip_input else "Ex: 192.168.43.1"
        ip_col = INK if self.ip_input else MUTED
        ip_surf = self.font_ip.render(ip_render, True, ip_col)
        surface.blit(ip_surf, ip_surf.get_rect(center=input_rect.center))

        # Bouton raccourci Hotspot Android
        qh_hovered = self.quick_hotspot_rect.collidepoint(self.mouse_pos)
        pygame.draw.rect(surface, PANEL_HOVER if qh_hovered else PANEL, self.quick_hotspot_rect, border_radius=10)
        pygame.draw.rect(surface, GOLD if qh_hovered else BORDER, self.quick_hotspot_rect, width=1, border_radius=10)
        qh_surf = self.font_small.render("Point d'accès Android standard (192.168.43.1)", True, GOLD)
        surface.blit(qh_surf, qh_surf.get_rect(center=self.quick_hotspot_rect.center))

        # Pavé numérique virtuel
        pad_title = self.font_small.render("Pavé tactile :", True, MUTED)
        surface.blit(pad_title, (70, 630))

        for key, krect in self.keypad_rects.items():
            k_hover = krect.collidepoint(self.mouse_pos)
            pygame.draw.rect(surface, PANEL_HOVER if k_hover else PANEL, krect, border_radius=8)
            pygame.draw.rect(surface, GOLD if k_hover else BORDER, krect, width=1, border_radius=8)
            col = GOLD if key == "Effacer" else INK
            f = self.font_small if key == "Effacer" else self.font_keypad
            lbl = f.render(key, True, col)
            surface.blit(lbl, lbl.get_rect(center=krect.center))

        # Statut / Erreur
        if self.status_message:
            st_surf = self.font_small.render(self.status_message, True, self.status_color)
            surface.blit(st_surf, st_surf.get_rect(center=(cx, 915)))

        # Bouton Se connecter
        c_hover = self.connect_rect.collidepoint(self.mouse_pos) and not self.connecting
        c_bg = PANEL_HOVER if c_hover else PANEL
        pygame.draw.rect(surface, c_bg, self.connect_rect, border_radius=12)
        pygame.draw.rect(surface, GOLD if c_hover else BORDER, self.connect_rect, width=2, border_radius=12)
        conn_label = "Connexion..." if self.connecting else "Se connecter"
        c_lbl = self.font_btn.render(conn_label, True, INK)
        surface.blit(c_lbl, c_lbl.get_rect(center=self.connect_rect.center))

        # Bouton Retour
        b_hover = self.back_rect.collidepoint(self.mouse_pos)
        if b_hover:
            pygame.draw.rect(surface, PANEL_HOVER, self.back_rect, border_radius=10)
        b_lbl = self.font_btn.render("Retour", True, INK if b_hover else MUTED)
        surface.blit(b_lbl, b_lbl.get_rect(center=self.back_rect.center))
