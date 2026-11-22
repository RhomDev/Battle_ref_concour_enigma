import hashlib
import random
from copy import copy
from pathlib import Path

from gameplay.card import CARD_KINDS, DATA, Card_Item
from gameplay.joueur import Joueur
from gameplay.terrain import Terrain


STARTING_HP = 15
MAX_ENERGY = 5
DRAW_COST = 1
OPENING_HAND = 4


class Catalogue:
    def __init__(self, data_root=DATA):
        self.cards = {}
        digest = hashlib.sha256()
        for folder in CARD_KINDS:
            for path in sorted((Path(data_root) / folder).glob("*.json")):
                card = Card_Item(path.name, folder, data_root=Path(data_root))
                if card.id in self.cards:
                    raise ValueError(f"Carte en double : {card.id}")
                self.cards[card.id] = card
                digest.update(f"{folder}/{path.name}\n".encode())
                digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
                digest.update(b"\n")
        self.fingerprint = digest.hexdigest()
        if (len(self.cards) < OPENING_HAND
                or not any(card.type == "character" for card in self.cards.values())
                or not any(getattr(card, "effect_type", None) == "attack" for card in self.cards.values())):
            raise ValueError("Le catalogue est incomplet.")

    def new_player(self, rng):
        deck = [copy(card) for card in self.cards.values()]
        rng.shuffle(deck)
        character = next(card for card in deck if card.type == "character")
        attack = next(card for card in deck if getattr(card, "effect_type", None) == "attack")
        deck.remove(character)
        deck.remove(attack)
        hand = [character, attack, deck.pop(), deck.pop()]
        rng.shuffle(hand)
        return Joueur(deck, hand, STARTING_HP)


class Partie:
    def __init__(self, catalogue, rng=None):
        rng = rng if rng is not None else random.Random()
        self.players = {seat: catalogue.new_player(rng) for seat in (1, 2)}
        self.terrain = Terrain()
        self.active = rng.choice((1, 2))
        self.players[self.active].energy = MAX_ENERGY
        self.turn = 1
        self.revision = 0
        self.result = None

    def targets(self, player, card):
        opponent = 3 - player
        if card.type == "character":
            return [(player, index) for index, slot in enumerate(self.terrain.slots[player]) if slot is None]
        target = opponent if card.effect_type == "attack" else player
        occupied = [(target, index) for index, slot in enumerate(self.terrain.slots[target]) if slot is not None]
        if card.effect_type == "attack" and not occupied:
            return [(opponent, None)]
        return occupied

    def apply(self, player, action):
        if self.result is not None:
            return "La partie est terminée."
        if type(player) is not int or player != self.active:
            return "Ce n’est pas votre tour."
        if not isinstance(action, dict) or type(action.get("revision")) is not int or action["revision"] != self.revision:
            return "Le plateau a changé. Réessayez."
        owner = self.players[player]
        kind = action.get("type")
        if kind == "pass":
            self.active = 3 - player
            self.players[self.active].energy = MAX_ENERGY
            self.turn += 1
        elif kind == "draw":
            if not owner.deck:
                return "Votre pioche est vide."
            if owner.energy < DRAW_COST:
                return "Énergie insuffisante."
            owner.hand.add_card(owner.deck.pop())
            owner.energy -= DRAW_COST
        elif kind == "play":
            error = self._play(player, action)
            if error:
                return error
        else:
            return "Action inconnue."

        self.revision += 1
        if self.result is None and all(not self._can_move(seat) for seat in self.players):
            self.result = "draw"
        return None

    def _play(self, player, action):
        owner = self.players[player]
        hand_index = action.get("card")
        if type(hand_index) is not int or not 0 <= hand_index < len(owner.hand.cards):
            return "Cette carte n’est pas dans votre main."
        card = owner.hand.cards[hand_index]
        if owner.energy < card.cost:
            return "Énergie insuffisante."
        target = action.get("target")
        index = action.get("slot")
        if ("slot" not in action or type(target) is not int or (index is not None and type(index) is not int)
                or (target, index) not in self.targets(player, card)):
            return "Cible invalide."

        if card.type == "character":
            self.terrain.place_card(player, card, index)
        elif index is not None:
            self.terrain.apply_effect(player, target, index, card)
        else:
            opponent = self.players[target]
            opponent.hp = max(0, opponent.hp - self.terrain.effect_amount(player, card))
            if opponent.hp == 0:
                self.result = player
        owner.hand.remove_card(card)
        owner.energy -= card.cost
        return None

    def _can_move(self, player):
        owner = self.players[player]
        return bool(owner.deck) or any(card.cost <= MAX_ENERGY and self.targets(player, card) for card in owner.hand.cards)

    def view(self, player):
        owner = self.players[player]
        can_act = self.result is None and player == self.active
        return {
            "seat": player,
            "active": self.active,
            "turn": self.turn,
            "revision": self.revision,
            "result": self.result,
            "max_energy": MAX_ENERGY,
            "draw_cost": DRAW_COST,
            "can_draw": can_act and owner.energy >= DRAW_COST and bool(owner.deck),
            "hand": [card.id for card in owner.hand.cards],
            "targets": [self.targets(player, card) if can_act and card.cost <= owner.energy else [] for card in owner.hand.cards],
            "players": [
                {
                    "seat": seat,
                    "hp": stats.hp,
                    "energy": stats.energy,
                    "hand_count": len(stats.hand.cards),
                    "deck_count": len(stats.deck),
                    "slots": [
                        {"id": card.id, "hp": card.hp, "shield": card.shield} if card else None
                        for card in self.terrain.slots[seat]
                    ],
                }
                for seat, stats in self.players.items()
            ],
        }

    def bot_action(self, player):
        owner = self.players[player]
        best = (0, {"type": "pass", "revision": self.revision})
        if owner.deck and owner.energy >= DRAW_COST:
            best = (2, {"type": "draw", "revision": self.revision})
        for hand_index, card in enumerate(owner.hand.cards):
            if card.cost > owner.energy:
                continue
            for target, index in self.targets(player, card):
                score = self._bot_score(player, card, target, index)
                if score > best[0]:
                    best = (score, {"type": "play", "revision": self.revision, "card": hand_index,
                                    "target": target, "slot": index})
        return best[1]

    def _bot_score(self, player, card, target, index):
        if card.type == "character":
            return 100 - card.cost
        amount = self.terrain.effect_amount(player, card)
        if index is None:
            return 90 if amount >= self.players[target].hp else 80 + min(amount, 9)
        slot = self.terrain.slots[target][index]
        if card.effect_type == "attack":
            return 70 if amount >= slot.hp + slot.shield else 40 + min(amount, 9)
        if card.effect_type == "heal":
            return 30 + min(amount, slot.hp_max - slot.hp, 9) if slot.hp < slot.hp_max else 1
        return 20 + min(amount, 9) if slot.shield < slot.hp_max else 1
