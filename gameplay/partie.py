import random
from gameplay.card import Card_Item
from gameplay.joueur import Joueur
from gameplay.terrain import Terrain


DRAW_COST = 1

DEFAULT_DECK_P1 = [
    ("macron.json", "card_perso"),
    ("luffy.json", "card_perso"),
    ("barbie.json", "card_perso"),
    ("saitama.json", "card_perso"),
    ("traverse_la_rue.json", "card_ref"),
    ("gear_fifth.json", "card_ref"),
    ("hi_barbie.json", "card_ref"),
    ("saitama_ok.json", "card_ref"),
    ("perlimpinpin.json", "card_ref"),
    ("ymca.json", "card_ref"),
    ("lucci_luffy_lunettes.json", "card_ref"),
    ("penser_a_la_mort.json", "card_ref"),
    ("saitama_moustique.json", "card_ref"),
    ("traverse_la_rue.json", "card_ref"),
    ("gear_fifth.json", "card_ref"),
    ("ymca.json", "card_ref"),
    ("lucci_luffy_lunettes.json", "card_ref"),
    ("saitama_moustique.json", "card_ref"),
    ("hi_barbie.json", "card_ref"),
    ("saitama_promos.json", "card_ref"),
    ("dango_luffy_kid.json", "card_ref"),
    ("saitama_moustique.json", "card_ref"),
]

DEFAULT_DECK_P2 = [
    ("vegeta.json", "card_perso"),
    ("creeper.json", "card_perso"),
    ("trump.json", "card_perso"),
    ("satoru_gojo.json", "card_perso"),
    ("bingo_vegeta.json", "card_ref"),
    ("creeper_aw_man.json", "card_ref"),
    ("wrong_trump.json", "card_ref"),
    ("gojo_domaine.json", "card_ref"),
    ("creeper_sifflement.json", "card_ref"),
    ("gojo_t_es_faible.json", "card_ref"),
    ("creeper_sifflement.json", "card_ref"),
    ("covfefe.json", "card_ref"),
    ("gojo_elu.json", "card_ref"),
    ("gojo_t_es_faible.json", "card_ref"),
    ("ymca.json", "card_ref"),
    ("creeper_aw_man.json", "card_ref"),
    ("creeper_sifflement.json", "card_ref"),
    ("gojo_elu.json", "card_ref"),
    ("wrong_trump.json", "card_ref"),
    ("covfefe.json", "card_ref"),
    ("creeper_sifflement.json", "card_ref"),
    ("gojo_elu.json", "card_ref"),
]


class Partie:
    def __init__(self, p1_name="Joueur 1", p2_name="Joueur 2", p1_hp=15, p2_hp=15):
        self.terrain = Terrain()
        self.players = {
            1: Joueur(1, name=p1_name, hp=p1_hp),
            2: Joueur(2, name=p2_name, hp=p2_hp),
        }
        self.current_turn = 1
        self.turn_number = 1
        self.game_over = False
        self.winner = None
        self.last_event = "La partie commence."
        self._init_decks()

    def _init_decks(self):
        deck1 = [Card_Item(f, cat) for f, cat in DEFAULT_DECK_P1]
        deck2 = [Card_Item(f, cat) for f, cat in DEFAULT_DECK_P2]
        random.shuffle(deck1)
        random.shuffle(deck2)
        self.players[1].deck = deck1
        self.players[2].deck = deck2

        # Initial draw: 4 cards for each player
        for _ in range(4):
            self.players[1].draw_card()
            self.players[2].draw_card()

    def play_character(self, player_id, hand_index, slot_index):
        if self.game_over:
            return False, "La partie est terminée."
        if player_id != self.current_turn:
            return False, "Ce n'est pas votre tour."

        player = self.players.get(player_id)
        if not player or type(hand_index) is not int or not (0 <= hand_index < len(player.hand.cards)):
            return False, "Carte introuvable en main."

        card = player.hand.cards[hand_index]
        if card.type != "character":
            return False, "La carte n'est pas un personnage."
        if not player.can_afford(card):
            return False, f"Énergie insuffisante (coût : {card.cost})."
        if not self.terrain.is_empty(player_id, slot_index):
            return False, "Emplacement occupé ou invalide."

        player.spend_energy(card.cost)
        player.hand.remove_card(card)
        self.terrain.place_card(player_id, card, slot_index)

        self.last_event = f"{player.name} a déployé {card.name}."
        return True, self.last_event

    def play_ref(self, player_id, hand_index, target_player, target_slot):
        if self.game_over:
            return False, "La partie est terminée."
        if player_id != self.current_turn:
            return False, "Ce n'est pas votre tour."

        player = self.players.get(player_id)
        if not player or type(hand_index) is not int or not (0 <= hand_index < len(player.hand.cards)):
            return False, "Carte introuvable en main."

        card = player.hand.cards[hand_index]
        if card.type != "ref":
            return False, "La carte n'est pas une référence."
        if not player.can_afford(card):
            return False, f"Énergie insuffisante (coût : {card.cost})."
        if type(target_player) is not int or target_player not in self.players:
            return False, "Joueur cible invalide."
        attack = card.effect_type == "attack"
        if attack and target_player == player_id:
            return False, "Une attaque doit cibler un personnage adverse."
        if card.effect_type in ("heal", "shield") and target_player != player_id:
            return False, "Un soin ou bouclier doit cibler un personnage allié."

        direct_attack = target_slot is None
        if direct_attack:
            if not attack:
                return False, "Cet effet doit cibler un personnage."
            if any(self.terrain.slots[target_player]):
                return False, "Les personnages adverses protègent les PV du joueur."
        else:
            if not self.terrain._has_slot(target_player, target_slot):
                return False, "Emplacement cible invalide."
            target_char = self.terrain.slots[target_player][target_slot]
            if target_char is None:
                return False, "Aucun personnage sur l'emplacement ciblé."
            if not self.terrain.apply_effect(player_id, target_player, target_slot, card):
                return False, "Effet invalide."

        player.spend_energy(card.cost)
        player.hand.remove_card(card)

        deployed_ids = [c.id for c in self.terrain.slots[player_id] if c is not None]
        amount = card.amount_with_synergy(deployed_ids)
        synergy_active = bool(card.synergy and card.synergy["character_id"] in deployed_ids)

        synergy_label = " [Synergie !]" if synergy_active else ""
        if direct_attack:
            opponent = self.players[target_player]
            if opponent.take_damage(amount) == 0:
                self.game_over = True
                self.winner = player_id
            desc = f"a infligé {amount} dégâts directs à {opponent.name}{synergy_label}."
        elif attack:
            ko_label = " (K.O. !)" if target_char.hp == 0 else ""
            desc = f"a infligé {amount} dégâts à {target_char.name}{synergy_label}{ko_label}."
        elif card.effect_type == "heal":
            desc = f"a soigné {target_char.name} de {amount} PV{synergy_label}."
        else:
            desc = f"a ajouté {amount} bouclier à {target_char.name}{synergy_label}."

        self.last_event = f"{player.name} {desc}"
        return True, self.last_event

    def draw_card(self, player_id):
        if self.game_over:
            return False, "La partie est terminée."
        if player_id != self.current_turn:
            return False, "Ce n'est pas votre tour."

        player = self.players[player_id]
        if not player.deck:
            return False, "La pioche est vide."
        if not player.spend_energy(DRAW_COST):
            return False, "Énergie insuffisante pour piocher."

        player.draw_card()
        self.last_event = f"{player.name} a pioché une carte."
        return True, self.last_event

    def pass_turn(self, player_id):
        if self.game_over:
            return False, "La partie est terminée."
        if player_id != self.current_turn:
            return False, "Ce n'est pas votre tour."

        next_id = 3 - player_id
        self.current_turn = next_id
        self.turn_number += 1
        active = self.players[next_id]
        active.reset_energy()
        self.last_event = f"Tour {self.turn_number} : Au tour de {active.name}."
        return True, self.last_event

    def play_bot_action(self, player_id):
        player = self.players[player_id]
        opponent_id = 3 - player_id
        allies = self.terrain.slots[player_id]
        opponents = self.terrain.slots[opponent_id]
        free_slot = next((i for i, card in enumerate(allies) if card is None), None)
        ally_slot = next((i for i, card in enumerate(allies) if card is not None), None)
        opponent_slot = next((i for i, card in enumerate(opponents) if card is not None), None)
        affordable = [(i, card) for i, card in enumerate(player.hand.cards) if player.can_afford(card)]

        if free_slot is not None:
            for i, card in affordable:
                if card.type == "character":
                    return self.play_character(player_id, i, free_slot)

        for i, card in affordable:
            if card.type == "ref" and card.effect_type == "attack":
                return self.play_ref(player_id, i, opponent_id, opponent_slot)

        if ally_slot is not None:
            for i, card in affordable:
                if card.type == "ref" and card.effect_type in ("heal", "shield"):
                    return self.play_ref(player_id, i, player_id, ally_slot)

        if player.deck and player.energy >= DRAW_COST:
            return self.draw_card(player_id)
        return self.pass_turn(player_id)

    def surrender(self, player_id):
        if not self.game_over:
            self.game_over = True
            self.winner = 3 - player_id
            self.last_event = f"{self.players[player_id].name} a abandonné."
            return True, self.last_event
        return False, "La partie est déjà terminée."

    def get_state_for_player(self, player_id):
        opponent_id = 3 - player_id
        return {
            "player_id": player_id,
            "current_turn": self.current_turn,
            "turn_number": self.turn_number,
            "game_over": self.game_over,
            "winner": self.winner,
            "last_event": self.last_event,
            "draw_cost": DRAW_COST,
            "you": self.players[player_id].to_dict(include_private=True),
            "opponent": self.players[opponent_id].to_dict(include_private=False),
            "terrain": self.terrain.to_dict(),
        }
