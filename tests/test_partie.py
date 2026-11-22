import unittest

from core.network import GameServer
from gameplay.card import Card_Item
from gameplay.partie import DRAW_COST, Partie


class PartieTest(unittest.TestCase):
    def setUp(self):
        self.partie = Partie()
        self.player = self.partie.players[1]
        self.opponent = self.partie.players[2]

    def test_character_knockout_does_not_damage_player(self):
        attack = Card_Item("ymca.json", "card_ref")
        self.player.hand.cards = [attack, attack]
        defender = Card_Item("creeper.json", "card_perso")
        self.partie.terrain.place_card(2, defender, 1)

        self.assertFalse(self.partie.play_ref(1, 0, 2, None)[0])
        self.assertEqual(self.player.energy, self.player.energy_max)
        self.assertEqual(len(self.player.hand.cards), 2)
        self.assertTrue(self.partie.play_ref(1, 0, 2, 1)[0])
        self.assertIsNone(self.partie.terrain.slots[2][1])
        self.assertEqual(self.opponent.hp, self.opponent.hp_max)

        self.assertTrue(self.partie.play_ref(1, 0, 2, None)[0])
        self.assertEqual(self.opponent.hp, self.opponent.hp_max - attack.amount)

    def test_direct_attack_uses_synergy_and_can_win(self):
        attack = Card_Item("gear_fifth.json", "card_ref")
        luffy = Card_Item("luffy.json", "card_perso")
        self.partie.terrain.place_card(1, luffy, 0)
        self.player.hand.cards = [attack]
        self.opponent.hp = attack.amount + attack.synergy["bonus"]

        self.assertFalse(self.partie.play_ref(1, 0, 1, None)[0])
        self.assertFalse(self.partie.play_ref(1, 0, 2, 0)[0])
        self.assertTrue(self.partie.play_ref(1, 0, 2, None)[0])
        self.assertEqual(self.opponent.hp, 0)
        self.assertTrue(self.partie.game_over)
        self.assertEqual(self.partie.winner, 1)

    def test_support_always_requires_a_character(self):
        for filename in ("hi_barbie.json", "bingo_vegeta.json"):
            with self.subTest(filename=filename):
                self.player.hand.cards = [Card_Item(filename, "card_ref")]
                self.assertFalse(self.partie.play_ref(1, 0, 1, None)[0])
                self.assertFalse(self.partie.play_ref(1, 0, 2, None)[0])
                self.assertEqual(self.player.energy, self.player.energy_max)

    def test_draw_spends_energy_and_keeps_card_private(self):
        server = GameServer()
        server.partie = self.partie
        drawn = self.player.deck[0]
        deck_size = len(self.player.deck)
        hand_size = len(self.player.hand.cards)

        server.submit_action(1, {"action": "draw_card", "cost": 0})
        host_state = server.poll_events()[0]["state"]
        remote_state = self.partie.get_state_for_player(2)
        self.assertEqual(host_state["you"]["energy"], self.player.energy_max - DRAW_COST)
        self.assertEqual(host_state["you"]["deck_count"], deck_size - 1)
        self.assertEqual(host_state["you"]["hand"][-1]["id"], drawn.id)
        self.assertEqual(remote_state["opponent"]["hand_count"], hand_size + 1)
        self.assertNotIn("hand", remote_state["opponent"])
        self.assertNotIn(drawn.name, remote_state["last_event"])

    def test_draw_rejections_do_not_charge_and_pass_does_not_draw(self):
        self.assertFalse(self.partie.draw_card(2)[0])
        self.player.energy = 0
        hand_size = len(self.player.hand.cards)
        self.assertFalse(self.partie.draw_card(1)[0])
        self.assertEqual(len(self.player.hand.cards), hand_size)

        self.player.energy = DRAW_COST
        self.player.deck.clear()
        self.assertFalse(self.partie.draw_card(1)[0])
        self.assertEqual(self.player.energy, DRAW_COST)
        opponent_hand_size = len(self.opponent.hand.cards)
        self.assertTrue(self.partie.pass_turn(1)[0])
        self.assertEqual(len(self.opponent.hand.cards), opponent_hand_size)
