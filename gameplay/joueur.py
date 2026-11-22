from gameplay.hand import Hand


class Joueur:
    def __init__(self, player_id, name="Joueur", hp=15, energy=5):
        self.id = player_id
        self.name = name
        self.hp_max = hp
        self.hp = hp
        self.energy_max = energy
        self.energy = energy
        self.deck = []
        self.hand = Hand()

    def draw_card(self):
        if self.deck:
            card = self.deck.pop(0)
            self.hand.add_card(card)
            return card
        return None

    def can_afford(self, card):
        return self.energy >= card.cost

    def spend_energy(self, amount):
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False

    def reset_energy(self):
        self.energy = self.energy_max

    def take_damage(self, amount):
        damage = max(0, amount)
        self.hp = max(0, self.hp - damage)
        return self.hp

    def heal(self, amount):
        self.hp = min(self.hp_max, self.hp + max(0, amount))
        return self.hp

    def to_dict(self, include_private=False):
        data = {
            "id": self.id,
            "name": self.name,
            "hp": self.hp,
            "hp_max": self.hp_max,
            "energy": self.energy,
            "energy_max": self.energy_max,
            "deck_count": len(self.deck),
            "hand_count": len(self.hand.cards),
        }
        if include_private:
            data["hand"] = [card.to_dict() for card in self.hand.cards]
        return data
