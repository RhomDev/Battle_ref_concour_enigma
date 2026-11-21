
import pygame


class Terrain:
    def __init__(self, game):
        self.game = game

        self.BACKGROUND = (20, 24, 36)
        self.PANEL = (29, 35, 51)

        # 3 cartes par joueur
        self.slots = {
            1: [None, None, None],
            2: [None, None, None]
        }

    # -------------------------
    # Gestion des cartes
    # -------------------------

    def place_card(self, player, card, index):
        if card.type != "character":
            return False

        if player not in self.slots or not 0 <= index < 3:
            return False

        if self.slots[player][index] is not None:
            return False

        self.slots[player][index] = card
        return True

    def remove_card(self, player, index):
        if player not in self.slots or not 0 <= index < 3:
            return False

        if self.slots[player][index] is None:
            return False

        self.slots[player][index] = None
        return True

    # -------------------------
    # Effets des cartes REF
    # -------------------------

    def apply_effect(self, player, target_player, index, ref_card):
        if ref_card.type != "ref":
            return False

        if target_player not in self.slots or not 0 <= index < 3:
            return False

        if player not in self.slots:
            return False

        card = self.slots[target_player][index]

        if card is None:
            return False

        ability = ref_card.ability
        amount = ref_card.amount

        if ability == "damage":
            if player == target_player:
                return False

            if card.take_damage(amount) <= 0:
                self.remove_card(target_player, index)

        elif ability == "heal":
            if player != target_player:
                return False
            card.heal(amount)

        elif ability == "shield":
            if player != target_player:
                return False
            card.shield(amount)

        else:
            return False

        return True

    # -------------------------
    # Détection des clics
    # -------------------------

    def get_clicked_card(self, mouse_pos):
        for player, slots in self.slots.items():
            for i, card in enumerate(slots):
                if card is not None and card.hitbox.collidepoint(mouse_pos):
                    return card, player, i

        return None, None, None

    # -------------------------
    # Affichage
    # -------------------------

    def draw(self, surface, local_player=1):
        surface.fill(self.BACKGROUND)

        W, H = surface.get_size()

        CARD_RATIO = 1.5

        card_width = min(W * 0.25, H * 0.25 / CARD_RATIO)
        card_height = card_width * CARD_RATIO
        spacing = card_width * 0.15

        total_width = 3 * card_width + 2 * spacing
        start_x = (W - total_width) / 2

        # Joueur local en bas, adversaire en haut
        enemy_player = 2 if local_player == 1 else 1

        for player, center_y in [
            (enemy_player, H * 0.28),
            (local_player, H * 0.72)
        ]:
            for i, card in enumerate(self.slots[player]):
                x = start_x + i * (card_width + spacing)
                y = center_y - card_height / 2

                rect = pygame.Rect(
                    round(x), round(y),
                    round(card_width), round(card_height)
                )

                if card is not None:
                    card.hitbox = rect.copy()
                    card.draw(surface, rect)
                else:
                    pygame.draw.rect(
                        surface, self.PANEL, rect,
                        border_radius=10
                    )
