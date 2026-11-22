import math
import pygame

from config import HEIGHT, WIDTH
from core.asset_manager import ROOT
from gameplay.card import Card_Item
from gameplay.partie import Partie
from gameplay.terrain import Terrain
from scenes.media_collection import GOLD, INK
from ui.Card_View import CARD_HEIGHT_RATIO, CardView
from ui.terain_ui import TerrainUI


MARGIN = 30
HAND_CARD_WIDTH = 130
HAND_CARD_GAP = 12
HAND_BOTTOM_MARGIN = 120
HAND_PAGE_SIZE = 5
ARENA_HEIGHT = 1054
SHADOW = (9, 16, 21)
METAL = (23, 36, 40)
METAL_EDGE = (119, 94, 61)
HEALTH_COLOR = (255, 167, 153)
GREEN = (72, 187, 120)
RED = (229, 62, 62)
CYAN = (100, 220, 240)
MUTED = (166, 173, 189)
BORDER = (59, 67, 83)


class BattleScene:
    def __init__(self, menu, mode="solo", server=None, client=None):
        self.menu = menu
        self.game = menu.game if menu else None
        self.mode = mode
        self.server = server
        self.client = client

        # Identification du joueur local
        if self.mode == "client":
            self.local_player_id = 2
        else:
            self.local_player_id = 1

        # Rectangles d'interface
        self.back_rect = pygame.Rect(MARGIN, 28, 146, 62)
        self.pass_rect = pygame.Rect(WIDTH - MARGIN - 184, self.back_rect.y, 184, self.back_rect.height)
        self.energy_rect = pygame.Rect(WIDTH - MARGIN - 246, HEIGHT - 100, 246, 72)
        self.draw_rect = pygame.Rect(MARGIN, self.energy_rect.y, 214, self.energy_rect.height)
        self.prev_hand_rect = pygame.Rect(257, self.energy_rect.y, 56, self.energy_rect.height)
        self.next_hand_rect = self.prev_hand_rect.move(63, 0)
        self.opponent_rect = pygame.Rect(0, 0, 460, 68)
        self.opponent_rect.center = (WIDTH // 2, 135)

        # Polices
        self.button_font = pygame.font.SysFont("arial", 26, bold=True)
        self.pass_font = pygame.font.SysFont("arial", 32, bold=True)
        self.event_font = pygame.font.SysFont("arial", 20, bold=True)
        self.status_font = pygame.font.SysFont("arial", 20, bold=True)
        self.overlay_title_font = pygame.font.SysFont("arial", 52, bold=True)
        self.overlay_sub_font = pygame.font.SysFont("arial", 26)

        self.pointer = (-1, -1)
        self.pass_highlight_until = 0
        self.card_view = CardView()
        self.terrain = Terrain()
        self.terrain_ui = TerrainUI(self.terrain, self.card_view)

        # Fond d'arène
        self.arena_background = self.make_arena_background()
        try:
            self.plaque_image = pygame.image.load(ROOT / "asset/board/plaque.webp")
        except Exception:
            self.plaque_image = None

        # État du jeu
        self.partie = None
        self.state = None
        self.hand_cards = []
        self.hand_rects = []
        self.hand_page = 0
        self.selected_hand_index = None
        self.action_error = ""
        self.disconnected = False
        self.disconnect_message = ""
        self.bot_timer = 0
        self.pulse_timer = 0

        # Initialisation selon le mode
        if self.mode == "solo":
            self.partie = Partie(p1_name="Vous", p2_name="IA Bot")
            self.state = self.partie.get_state_for_player(1)
            self._update_from_state(self.state)
        elif self.mode == "host":
            # Le serveur gère la partie
            self.state = self.server.partie.get_state_for_player(1)
            self._update_from_state(self.state)
        elif self.mode == "client":
            # Attente de la première synchronisation du serveur
            pass

    @staticmethod
    def make_arena_background():
        background = pygame.Surface((WIDTH, HEIGHT))
        background.fill(SHADOW)
        try:
            arena = pygame.image.load(ROOT / "asset/board/theatre-des-echos.webp")
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
        except Exception:
            pass
        return background

    def to_canvas_position(self, pos):
        if self.menu:
            return self.menu.to_canvas_position(pos)
        return pos

    def _update_from_state(self, state):
        self.state = state
        self.action_error = ""
        # Reconstruction des cartes du terrain
        t_data = state.get("terrain", {})
        for p in (1, 2):
            slots_data = t_data.get(str(p), t_data.get(p, [None, None, None]))
            for i, c_data in enumerate(slots_data):
                if c_data:
                    self.terrain.slots[p][i] = Card_Item.from_dict(c_data)
                else:
                    self.terrain.slots[p][i] = None

        # Reconstruction de la main locale
        hand_data = state.get("you", {}).get("hand", [])
        self.hand_cards = [Card_Item.from_dict(c) for c in hand_data]
        self.hand_page = min(self.hand_page, self.hand_page_count - 1)
        self._layout_hand()

        if self.selected_hand_index is not None and self.selected_hand_index >= len(self.hand_cards):
            self.selected_hand_index = None

    @property
    def hand_page_count(self):
        return max(1, math.ceil(len(self.hand_cards) / HAND_PAGE_SIZE))

    def _layout_hand(self):
        card_height = round(HAND_CARD_WIDTH * CARD_HEIGHT_RATIO)
        hand_top = HEIGHT - HAND_BOTTOM_MARGIN - card_height
        start = self.hand_page * HAND_PAGE_SIZE
        count = min(HAND_PAGE_SIZE, len(self.hand_cards) - start)
        total_width = count * HAND_CARD_WIDTH + max(0, count - 1) * HAND_CARD_GAP
        start_x = (WIDTH - total_width) // 2

        self.hand_rects = []
        for i in range(count):
            rx = start_x + i * (HAND_CARD_WIDTH + HAND_CARD_GAP)
            rect = pygame.Rect(rx, hand_top, HAND_CARD_WIDTH, card_height)
            self.hand_rects.append((start + i, rect))

    def can_draw(self):
        you = self.state["you"]
        cost = self.state.get("draw_cost")
        return (
            cost is not None
            and self.state["current_turn"] == self.local_player_id
            and not self.state["game_over"]
            and not self.disconnected
            and you["deck_count"] > 0
            and you["energy"] >= cost
        )

    def direct_target(self):
        if (
            self.selected_hand_index is None
            or self.state["current_turn"] != self.local_player_id
            or self.state["game_over"]
            or self.disconnected
        ):
            return None
        card = self.hand_cards[self.selected_hand_index]
        opponent_id = 3 - self.local_player_id
        if (
            card.type == "ref"
            and card.effect_type == "attack"
            and card.cost <= self.state["you"]["energy"]
            and not any(self.terrain.slots[opponent_id])
        ):
            return opponent_id
        return None

    def send_action(self, action_data):
        self.action_error = ""
        if self.mode == "solo":
            p_id = self.local_player_id
            act = action_data.get("action")
            if act == "play_character":
                ok, message = self.partie.play_character(p_id, action_data["hand_index"], action_data["slot_index"])
            elif act == "play_ref":
                ok, message = self.partie.play_ref(
                    p_id, action_data["hand_index"], action_data["target_player"], action_data["target_slot"]
                )
            elif act == "draw_card":
                ok, message = self.partie.draw_card(p_id)
            elif act == "pass_turn":
                ok, message = self.partie.pass_turn(p_id)
            else:
                return
            if ok:
                self._update_from_state(self.partie.get_state_for_player(p_id))
            else:
                self.action_error = message

        elif self.mode == "host":
            if self.server:
                self.server.submit_action(1, action_data)

        elif self.mode == "client":
            if self.client:
                self.client.send_action(action_data)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.cleanup_and_exit()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.to_canvas_position(event.pos)

            # Clic sur le bouton Menu
            if self.back_rect.collidepoint(pos):
                self.cleanup_and_exit()
                return

            # Si fin de partie ou déconnexion, clic sur le bouton de retour de l'overlay
            if self.disconnected or (self.state and self.state.get("game_over")):
                modal_btn = pygame.Rect((WIDTH - 280) // 2, HEIGHT // 2 + 70, 280, 58)
                if modal_btn.collidepoint(pos):
                    self.cleanup_and_exit()
                    return

            if not self.state:
                return

            current_turn = self.state.get("current_turn")
            is_my_turn = (current_turn == self.local_player_id)

            if self.draw_rect.collidepoint(pos):
                if self.can_draw():
                    self.selected_hand_index = None
                    self.send_action({"action": "draw_card"})
                return

            if self.hand_page_count > 1:
                change_page = int(self.next_hand_rect.collidepoint(pos)) - int(self.prev_hand_rect.collidepoint(pos))
                if change_page:
                    self.hand_page = max(0, min(self.hand_page + change_page, self.hand_page_count - 1))
                    self.selected_hand_index = None
                    self._layout_hand()
                    return

            # Clic sur le bouton Passer
            if self.pass_rect.collidepoint(pos) and is_my_turn:
                self.pass_highlight_until = pygame.time.get_ticks() + 240
                self.send_action({"action": "pass_turn"})
                self.selected_hand_index = None
                return

            # Clic sur les cartes de la main
            clicked_hand = False
            for idx, rect in self.hand_rects:
                if rect.collidepoint(pos):
                    clicked_hand = True
                    if self.selected_hand_index == idx:
                        self.selected_hand_index = None  # Désélection
                    else:
                        self.selected_hand_index = idx
                    break

            if clicked_hand:
                return

            direct_target = self.direct_target()
            if direct_target is not None and self.opponent_rect.collidepoint(pos):
                self.send_action({
                    "action": "play_ref",
                    "hand_index": self.selected_hand_index,
                    "target_player": direct_target,
                    "target_slot": None,
                })
                self.selected_hand_index = None
                return

            # Clic sur les emplacements du plateau si une carte est sélectionnée
            if self.selected_hand_index is not None and is_my_turn:
                card = self.hand_cards[self.selected_hand_index]
                target_p, target_slot, target_c, _ = self.terrain_ui.get_slot_at(
                    pos, (WIDTH, HEIGHT), local_player=self.local_player_id
                )

                if target_slot is not None:
                    if card.type == "character":
                        # Déploiement sur un emplacement allié vide
                        if target_p == self.local_player_id and target_c is None:
                            self.send_action({
                                "action": "play_character",
                                "hand_index": self.selected_hand_index,
                                "slot_index": target_slot,
                            })
                            self.selected_hand_index = None
                    elif card.type == "ref":
                        if card.effect_type == "attack":
                            # Attaque sur un personnage adverse
                            if target_p != self.local_player_id and target_c is not None:
                                self.send_action({
                                    "action": "play_ref",
                                    "hand_index": self.selected_hand_index,
                                    "target_player": target_p,
                                    "target_slot": target_slot,
                                })
                                self.selected_hand_index = None
                        elif card.effect_type in ("heal", "shield"):
                            # Soin / Bouclier sur un personnage allié
                            if target_p == self.local_player_id and target_c is not None:
                                self.send_action({
                                    "action": "play_ref",
                                    "hand_index": self.selected_hand_index,
                                    "target_player": target_p,
                                    "target_slot": target_slot,
                                })
                                self.selected_hand_index = None
                    return

            # Clic dans le vide -> désélection
            self.selected_hand_index = None

    def cleanup_and_exit(self):
        if self.mode == "host" and self.server:
            self.server.stop()
            self.server = None
        elif self.mode == "client" and self.client:
            self.client.disconnect()
            self.client = None

        if self.game and self.menu:
            self.game.change_scene(self.menu)

    def update(self, dt):
        self.pointer = self.to_canvas_position(pygame.mouse.get_pos())
        self.pulse_timer += dt

        # Traitement des événements en mode Solo (IA Bot)
        if self.mode == "solo" and self.partie and not self.partie.game_over:
            if self.partie.current_turn == 2:
                self.bot_timer += dt
                if self.bot_timer > 1.2:
                    self.partie.play_bot_action(2)
                    self._update_from_state(self.partie.get_state_for_player(1))
                    self.bot_timer = 0
            else:
                self.bot_timer = 0

        # Traitement des événements en mode Hôte
        elif self.mode == "host" and self.server:
            events = self.server.poll_events()
            for ev in events:
                ev_type = ev.get("type")
                if ev_type == "state_update":
                    self._update_from_state(ev["state"])
                elif ev_type == "error":
                    self.action_error = ev["message"]
                elif ev_type == "opponent_disconnected":
                    self.disconnected = True
                    self.disconnect_message = ev.get("message", "Le joueur 2 s'est déconnecté.")

        # Traitement des événements en mode Client
        elif self.mode == "client" and self.client:
            events = self.client.poll_events()
            for ev in events:
                ev_type = ev.get("type")
                if ev_type == "state_update":
                    self._update_from_state(ev["state"])
                elif ev_type == "action_error":
                    self.action_error = ev["message"]
                elif ev_type in ("disconnected", "opponent_disconnected"):
                    self.disconnected = True
                    self.disconnect_message = ev.get("message", "Connexion avec l'hôte perdue.")

    def draw(self, surface):
        surface.blit(self.arena_background, (0, 0))

        if not self.state:
            # Écran d'attente initial
            self.draw_waiting_screen(surface)
            return

        # 1. En-tête : Bouton Menu, Badge réseau, Bouton Passer
        self.draw_header(surface)

        # 2. Barre Adversaire (Nom, PV, Énergie, Cartes)
        self.draw_opponent_bar(surface)

        # 3. Plateau de jeu (TerrainUI)
        self.terrain_ui.draw(surface, local_player=self.local_player_id, fill_background=False)

        # 4. Surbrillance des emplacements éligibles
        self.draw_slot_highlights(surface)

        # 5. Bandeau central : Tour et Dernier événement
        self.draw_center_banner(surface)

        # 6. Barre Joueur local (Nom, PV)
        self.draw_player_bar(surface)

        # 7. Main du joueur local
        self.draw_hand(surface)

        # 8. Pioche, navigation dans la main et énergie
        self.draw_hand_controls(surface)
        self.draw_energy(surface)

        # 9. Modales de Fin de partie ou Déconnexion
        if self.disconnected:
            self.draw_modal_overlay(surface, "DÉCONNEXION", self.disconnect_message, RED)
        elif self.state.get("game_over"):
            winner = self.state.get("winner")
            is_win = (winner == self.local_player_id)
            title = "VICTOIRE !" if is_win else "DÉFAITE"
            color = GOLD if is_win else RED
            sub = "Vous avez terrassé l'adversaire !" if is_win else "Vos points de vie sont épuisés."
            self.draw_modal_overlay(surface, title, sub, color)

    def draw_header(self, surface):
        # Bouton Menu
        back_col = (36, 52, 55) if self.back_rect.collidepoint(self.pointer) else METAL
        pygame.draw.rect(surface, back_col, self.back_rect, border_radius=12)
        pygame.draw.rect(surface, METAL_EDGE, self.back_rect, width=2, border_radius=12)
        bx, by = self.back_rect.left + 23, self.back_rect.centery
        pygame.draw.lines(surface, GOLD, False, [(bx + 6, by - 7), (bx, by), (bx + 6, by + 7)], 2)
        txt = self.button_font.render("Menu", True, INK)
        surface.blit(txt, txt.get_rect(center=(self.back_rect.centerx + 10, by)))

        # Badge Réseau
        net_rect = pygame.Rect((WIDTH - 220) // 2, self.back_rect.y + 12, 220, 38)
        pygame.draw.rect(surface, (18, 24, 34, 200), net_rect, border_radius=19)
        pygame.draw.rect(surface, BORDER, net_rect, width=1, border_radius=19)

        if self.mode == "solo":
            badge_txt = "Mode Solo"
            dot_col = MUTED
        elif self.mode == "host":
            badge_txt = "Hôte (J1)"
            dot_col = GREEN
        else:
            badge_txt = "Client (J2)"
            dot_col = GREEN

        pygame.draw.circle(surface, dot_col, (net_rect.left + 22, net_rect.centery), 6)
        b_surf = self.status_font.render(badge_txt, True, INK)
        surface.blit(b_surf, (net_rect.left + 38, net_rect.top + 7))

        # Bouton Passer
        current_turn = self.state.get("current_turn")
        is_my_turn = (current_turn == self.local_player_id)
        pressed = pygame.time.get_ticks() < self.pass_highlight_until
        pass_hover = self.pass_rect.collidepoint(self.pointer) and is_my_turn

        if not is_my_turn:
            pass_bg = (30, 36, 46)
            pass_edge = BORDER
            pass_text = "Attente..."
            pass_txt_col = MUTED
        else:
            pass_bg = (161, 111, 54) if pressed else GOLD if pass_hover else (203, 152, 75)
            pass_edge = (246, 213, 147)
            pass_text = "Passer"
            pass_txt_col = SHADOW

        pygame.draw.rect(surface, pass_bg, self.pass_rect, border_radius=12)
        pygame.draw.rect(surface, pass_edge, self.pass_rect, width=2, border_radius=12)
        p_surf = self.pass_font.render(pass_text, True, pass_txt_col)
        surface.blit(p_surf, p_surf.get_rect(center=self.pass_rect.center))

    def draw_opponent_bar(self, surface):
        opp = self.state.get("opponent", {})
        opp_name = opp.get("name", "Adversaire")
        opp_hp = opp.get("hp", 0)
        opp_energy = opp.get("energy", 0)
        opp_hand_cnt = opp.get("hand_count", 0)

        plate_rect = self.opponent_rect

        if self.plaque_image:
            plate = pygame.transform.smoothscale(self.plaque_image, plate_rect.size)
            surface.blit(plate, plate_rect)
        else:
            pygame.draw.rect(surface, METAL, plate_rect, border_radius=10)
            pygame.draw.rect(surface, METAL_EDGE, plate_rect, width=2, border_radius=10)

        name_surf = self.button_font.render(opp_name, True, INK)
        hp_surf = self.button_font.render(f"{opp_hp} PV", True, HEALTH_COLOR)
        cards_surf = self.status_font.render(f"Main : {opp_hand_cnt}", True, MUTED)
        eng_surf = self.status_font.render(f"⚡ {opp_energy}", True, CYAN)

        surface.blit(name_surf, (plate_rect.left + 24, plate_rect.top + 20))
        surface.blit(hp_surf, (plate_rect.left + 160, plate_rect.top + 20))
        surface.blit(eng_surf, (plate_rect.left + 260, plate_rect.top + 22))
        surface.blit(cards_surf, (plate_rect.left + 340, plate_rect.top + 22))

        if self.direct_target() is not None:
            pygame.draw.rect(surface, RED, plate_rect, width=2, border_radius=10)
            target_label = self.status_font.render("Attaque directe", True, INK)
            surface.blit(target_label, target_label.get_rect(midtop=(plate_rect.centerx, plate_rect.bottom + 4)))

    def draw_player_bar(self, surface):
        you = self.state.get("you", {})
        you_name = you.get("name", "Vous")
        you_hp = you.get("hp", 0)

        center_y = HEIGHT - 370
        plate_rect = pygame.Rect(0, 0, 320, 56)
        plate_rect.center = (WIDTH // 2, center_y)

        if self.plaque_image:
            plate = pygame.transform.smoothscale(self.plaque_image, plate_rect.size)
            surface.blit(plate, plate_rect)
        else:
            pygame.draw.rect(surface, METAL, plate_rect, border_radius=10)
            pygame.draw.rect(surface, METAL_EDGE, plate_rect, width=2, border_radius=10)

        name_surf = self.button_font.render(you_name, True, INK)
        hp_surf = self.button_font.render(f"{you_hp} PV", True, HEALTH_COLOR)

        gap = 20
        total_w = name_surf.get_width() + gap + hp_surf.get_width()
        start_x = plate_rect.centerx - total_w // 2

        surface.blit(name_surf, (start_x, plate_rect.top + 14))
        surface.blit(hp_surf, (start_x + name_surf.get_width() + gap, plate_rect.top + 14))

    def draw_center_banner(self, surface):
        current_turn = self.state.get("current_turn")
        is_my_turn = (current_turn == self.local_player_id)
        cx = WIDTH // 2
        cy = HEIGHT // 2 - 20

        # Indicateur de Tour
        turn_text = "★ VOTRE TOUR ★" if is_my_turn else "TOUR DE L'ADVERSAIRE"
        turn_color = GOLD if is_my_turn else MUTED
        t_surf = self.button_font.render(turn_text, True, turn_color)
        t_rect = t_surf.get_rect(center=(cx, cy - 18))

        # Fond subtil sous l'indicateur
        bg_rect = t_rect.inflate(36, 12)
        pygame.draw.rect(surface, (14, 18, 28, 180), bg_rect, border_radius=8)
        pygame.draw.rect(surface, turn_color if is_my_turn else BORDER, bg_rect, width=1, border_radius=8)
        surface.blit(t_surf, t_rect)

        # Dernier événement
        last_ev = self.action_error or self.state.get("last_event", "")
        if last_ev:
            ev_surf = self.event_font.render(last_ev, True, INK)
            surface.blit(ev_surf, ev_surf.get_rect(center=(cx, cy + 22)))

    def draw_slot_highlights(self, surface):
        if self.selected_hand_index is None or not (0 <= self.selected_hand_index < len(self.hand_cards)):
            return

        card = self.hand_cards[self.selected_hand_index]
        pulse = (math.sin(self.pulse_timer * 6) + 1) / 2
        glow_width = int(2 + pulse * 2)

        for p, idx, c, rect in self.terrain_ui.positions((WIDTH, HEIGHT), local_player=self.local_player_id):
            if card.type == "character":
                # Emplacements alliés libres
                if p == self.local_player_id and c is None:
                    pygame.draw.rect(surface, GREEN, rect.inflate(8, 8), width=glow_width, border_radius=12)
            elif card.type == "ref":
                if card.effect_type == "attack":
                    # Personnages adverses ciblables
                    if p != self.local_player_id and c is not None:
                        pygame.draw.rect(surface, RED, rect.inflate(8, 8), width=glow_width, border_radius=12)
                elif card.effect_type in ("heal", "shield"):
                    # Personnages alliés ciblables
                    if p == self.local_player_id and c is not None:
                        pygame.draw.rect(surface, CYAN, rect.inflate(8, 8), width=glow_width, border_radius=12)

    def draw_hand(self, surface):
        you_energy = self.state.get("you", {}).get("energy", 0)

        for idx, rect in self.hand_rects:
            card = self.hand_cards[idx]
            is_selected = (self.selected_hand_index == idx)

            draw_rect = rect.move(0, -18) if is_selected else rect
            self.card_view.draw(surface, draw_rect, card)

            # Cadre de sélection
            if is_selected:
                pygame.draw.rect(surface, GOLD, draw_rect.inflate(8, 8), width=3, border_radius=12)

            # Assombrir si énergie insuffisante
            if card.cost > you_energy:
                dim_overlay = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
                dim_overlay.fill((0, 0, 0, 110))
                surface.blit(dim_overlay, draw_rect.topleft)

    def draw_hand_controls(self, surface):
        active = self.can_draw()
        hovered = active and self.draw_rect.collidepoint(self.pointer)
        fill = (46, 66, 68) if hovered else METAL
        pygame.draw.rect(surface, fill, self.draw_rect, border_radius=12)
        pygame.draw.rect(surface, METAL_EDGE if active else BORDER, self.draw_rect, width=1, border_radius=12)
        deck_count = self.state["you"]["deck_count"]
        cost = self.state.get("draw_cost")
        label = self.button_font.render(f"Piocher ({deck_count})", True, INK if active else MUTED)
        surface.blit(label, label.get_rect(center=(self.draw_rect.centerx, self.draw_rect.centery - 12)))
        if cost is not None:
            price = self.status_font.render(f"{cost} énergie", True, GOLD if active else MUTED)
            surface.blit(price, price.get_rect(center=(self.draw_rect.centerx, self.draw_rect.centery + 15)))

        if self.hand_page_count > 1:
            for rect, direction, enabled in (
                (self.prev_hand_rect, -1, self.hand_page > 0),
                (self.next_hand_rect, 1, self.hand_page + 1 < self.hand_page_count),
            ):
                pygame.draw.rect(surface, METAL, rect, border_radius=12)
                pygame.draw.rect(surface, METAL_EDGE if enabled else BORDER, rect, width=1, border_radius=12)
                x, y = rect.center
                points = [(x - 4 * direction, y - 8), (x + 4 * direction, y), (x - 4 * direction, y + 8)]
                pygame.draw.lines(surface, GOLD if enabled else MUTED, False, points, 2)
            page = self.status_font.render(f"{self.hand_page + 1}/{self.hand_page_count}", True, INK)
            surface.blit(page, page.get_rect(center=(408, self.energy_rect.centery)))

    def draw_energy(self, surface):
        rect = self.energy_rect
        you_energy = self.state.get("you", {}).get("energy", 0)
        you_energy_max = self.state.get("you", {}).get("energy_max", 5)

        pygame.draw.rect(surface, METAL, rect, border_radius=12)
        pygame.draw.rect(surface, METAL_EDGE, rect, width=1, border_radius=12)

        # Gemme cyan
        x, y = rect.left + 29, rect.centery
        gem = [(x, y - 14), (x + 9, y), (x, y + 14), (x - 9, y)]
        pygame.draw.polygon(surface, (142, 205, 205), gem, width=2)

        lbl = self.button_font.render("Énergie", True, INK)
        surface.blit(lbl, lbl.get_rect(midleft=(rect.left + 50, y)))

        val = self.button_font.render(f"{you_energy} / {you_energy_max}", True, GOLD)
        surface.blit(val, val.get_rect(midright=(rect.right - 18, y)))

    def draw_waiting_screen(self, surface):
        cx, cy = WIDTH // 2, HEIGHT // 2
        txt = self.overlay_sub_font.render("Connexion et synchronisation en cours...", True, GOLD)
        surface.blit(txt, txt.get_rect(center=(cx, cy)))

    def draw_modal_overlay(self, surface, title, subtitle, color):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 14, 22, 220))
        surface.blit(overlay, (0, 0))

        cx, cy = WIDTH // 2, HEIGHT // 2
        t_surf = self.overlay_title_font.render(title, True, color)
        surface.blit(t_surf, t_surf.get_rect(center=(cx, cy - 60)))

        s_surf = self.overlay_sub_font.render(subtitle, True, INK)
        surface.blit(s_surf, s_surf.get_rect(center=(cx, cy)))

        btn_rect = pygame.Rect((WIDTH - 280) // 2, cy + 70, 280, 58)
        hovered = btn_rect.collidepoint(self.pointer)
        pygame.draw.rect(surface, (39, 48, 65) if hovered else (29, 35, 51), btn_rect, border_radius=12)
        pygame.draw.rect(surface, GOLD if hovered else BORDER, btn_rect, width=2, border_radius=12)

        btn_txt = self.button_font.render("Retour au menu", True, INK)
        surface.blit(btn_txt, btn_txt.get_rect(center=btn_rect.center))
