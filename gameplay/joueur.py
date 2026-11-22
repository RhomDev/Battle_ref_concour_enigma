from gameplay.hand import Hand


class Joueur:
    def __init__(self, deck, opening_hand, hp):
        self.deck = deck
        self.hand = Hand()
        for card in opening_hand:
            self.hand.add_card(card)
        self.hp = hp
        self.energy = 0
