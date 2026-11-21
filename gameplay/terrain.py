class Terrain:
    def __init__(self):
        self.slots = {
            1: [None, None, None],
            2: [None, None, None],
        }

    def _has_slot(self, player, index):
        return (
            type(player) is int
            and player in self.slots
            and type(index) is int
            and 0 <= index < len(self.slots[player])
        )

    def place_card(self, player, card, index):
        if card.type != "character" or not self._has_slot(player, index):
            return False
        if self.slots[player][index] is not None:
            return False

        self.slots[player][index] = card
        return True

    def remove_card(self, player, index):
        if not self._has_slot(player, index) or self.slots[player][index] is None:
            return False

        self.slots[player][index] = None
        return True

    def apply_effect(self, player, target_player, index, ref_card):
        if ref_card.type != "ref" or type(player) is not int or player not in self.slots:
            return False
        if not self._has_slot(target_player, index):
            return False

        target = self.slots[target_player][index]
        if target is None:
            return False

        effect_type = ref_card.effect_type
        allowed_target = {
            "attack": target_player != player,
            "heal": target_player == player,
            "shield": target_player == player,
        }
        if not allowed_target.get(effect_type, False):
            return False

        deployed_ids = (card.id for card in self.slots[player] if card is not None)
        amount = ref_card.amount_with_synergy(deployed_ids)

        if effect_type == "attack":
            if target.take_damage(amount) == 0:
                self.remove_card(target_player, index)
        elif effect_type == "heal":
            target.heal(amount)
        else:
            target.add_shield(amount)
        return True
