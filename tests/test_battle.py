import json
import socket
import unittest
from copy import copy
from random import Random
from time import monotonic, sleep

from core.battle_session import BattleSession, VERSION
from gameplay.partie import Catalogue, Partie


class RulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue = Catalogue()

    def setUp(self):
        self.game = Partie(self.catalogue, Random(1))
        self.one, self.two = self.game.players.values()

    def card(self, card_id):
        return copy(self.catalogue.cards[card_id])

    def apply(self, player, kind, **data):
        return self.game.apply(player, {"type": kind, "revision": self.game.revision, **data})

    def play(self, player, card_id, target, slot):
        owner = self.game.players[player]
        owner.hand.cards[:] = [self.card(card_id)]
        return self.apply(player, "play", card=0, target=target, slot=slot)

    def test_opening_draw_and_pass_at_zero_energy(self):
        for owner in (self.one, self.two):
            self.assertEqual(owner.hp, 15)
            self.assertEqual(len(owner.hand.cards), 4)
            self.assertEqual(len(owner.deck) + len(owner.hand.cards), len(self.catalogue.cards))
            self.assertTrue(any(card.type == "character" for card in owner.hand.cards))
            self.assertTrue(any(getattr(card, "effect_type", None) == "attack" for card in owner.hand.cards))
        self.assertTrue(all(slot is None for row in self.game.terrain.slots.values() for slot in row))
        active = self.game.active
        owner = self.game.players[active]
        self.assertEqual(owner.energy, 5)
        self.assertIsNone(self.apply(active, "draw"))
        self.assertEqual((len(owner.hand.cards), owner.energy), (5, 4))
        owner.energy = 0
        self.assertIsNotNone(self.apply(active, "draw"))
        self.assertIsNone(self.apply(active, "pass"))
        self.assertEqual(self.game.active, 3 - active)
        self.assertEqual(self.game.players[3 - active].energy, 5)

    def test_rejected_actions_preserve_the_state(self):
        self.game.active = 1
        self.one.energy = 1
        self.one.hand.cards[:] = [self.card("macron")]
        before = self.game.view(1)
        self.assertIsNotNone(self.apply(2, "pass"))
        self.assertIsNotNone(self.apply(1, "play", card=0, target=1, slot=0))
        self.assertIsNotNone(self.game.apply(1, {"type": "pass", "revision": True}))
        self.assertEqual(before, self.game.view(1))

    def test_deploy_shield_attack_heal_and_synergy(self):
        self.game.active = 1
        self.one.energy = 5
        self.assertIsNone(self.play(1, "vegeta", 1, 0))
        vegeta = self.game.terrain.slots[1][0]
        self.one.energy = 5
        self.assertIsNotNone(self.play(1, "macron", 1, 0))
        shield_ref = self.card("touche_pas_bulma")
        self.assertIsNone(self.play(1, shield_ref.id, 1, 0))
        self.assertEqual(vegeta.shield, shield_ref.amount + shield_ref.synergy["bonus"])
        self.assertIsNone(self.apply(1, "pass"))
        attack = self.card("ymca")
        self.assertIsNotNone(self.play(2, attack.id, 1, None))
        self.assertIsNone(self.play(2, attack.id, 1, 0))
        self.assertEqual(vegeta.hp, vegeta.hp_max)
        self.assertEqual(vegeta.shield, shield_ref.amount + shield_ref.synergy["bonus"] - attack.amount)
        self.assertIsNone(self.apply(2, "pass"))
        vegeta.hp = vegeta.hp_max - 1
        self.assertIsNone(self.play(1, "giorno_soigne_mista", 1, 0))
        self.assertEqual(vegeta.hp, vegeta.hp_max)

    def test_last_character_blocks_player_damage_until_next_attack(self):
        self.game.active = 1
        self.one.energy = 5
        self.game.terrain.place_card(1, self.card("trump"), 0)
        self.game.terrain.place_card(2, self.card("creeper"), 0)
        attack = self.card("ymca")
        self.two.hp = attack.amount + attack.synergy["bonus"]
        self.assertIsNone(self.play(1, attack.id, 2, 0))
        self.assertIsNone(self.game.terrain.slots[2][0])
        self.assertEqual(self.two.hp, attack.amount + attack.synergy["bonus"])
        self.one.energy = 5
        self.assertIsNone(self.play(1, attack.id, 2, None))
        self.assertEqual(self.two.hp, 0)
        self.assertEqual(self.game.result, 1)
        self.assertIsNotNone(self.apply(1, "pass"))

    def test_draw_requires_both_players_to_be_blocked_at_full_energy(self):
        for owner in (self.one, self.two):
            owner.deck.clear()
            owner.hand.cards[:] = [self.card("giorno_soigne_mista")]
        self.two.hand.cards.append(self.card("creeper"))
        self.assertIsNone(self.apply(self.game.active, "pass"))
        self.assertIsNone(self.game.result)
        self.two.hand.cards.pop()
        self.assertIsNone(self.apply(self.game.active, "pass"))
        self.assertEqual(self.game.result, "draw")

    def test_bot_games_reach_an_outcome(self):
        for seed in range(20):
            with self.subTest(seed=seed):
                game = Partie(self.catalogue, Random(seed))
                for _ in range(500):
                    if game.result is not None:
                        break
                    self.assertIsNone(game.apply(game.active, game.bot_action(game.active)))
                self.assertIsNotNone(game.result)


class NetworkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue = Catalogue()

    def event(self, session, kind, timeout=4):
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            event = session._take(session.events)
            if event and event["type"] == kind:
                return event["value"]
            sleep(0.01)
        self.fail(f"Événement absent : {kind}")

    def session(self, mode, port):
        session = BattleSession(self.catalogue, mode, "127.0.0.1", port=port)
        self.addCleanup(session.worker.join, 2)
        self.addCleanup(session.close)
        return session

    def test_two_players_get_private_views_and_can_pass_and_disconnect(self):
        host = self.session("host", 0)
        port = self.event(host, "waiting")["port"]
        guest = self.session("join", port)
        home = self.event(host, "state")
        away = self.event(guest, "state")
        self.assertEqual((home["seat"], away["seat"]), (1, 2))
        self.assertEqual(home["players"], away["players"])
        for view in (home, away):
            self.assertEqual(len(view["hand"]), 4)
            for stats in view["players"]:
                self.assertNotIn("hand", stats)
                self.assertNotIn("deck", stats)
        third = self.session("join", port)
        self.assertIn("complète", self.event(third, "closed"))
        active, inactive = (host, guest) if home["active"] == 1 else (guest, host)
        inactive.submit({"type": "pass", "revision": home["revision"]})
        self.assertIn("tour", self.event(inactive, "error"))
        active.submit({"type": "pass", "revision": home["revision"]})
        new_home = self.event(host, "state")
        new_away = self.event(guest, "state")
        self.assertEqual(new_home["turn"], 2)
        self.assertEqual(new_away["active"], 3 - home["active"])
        self.assertEqual(new_home["players"], new_away["players"])
        guest.close()
        self.assertIn("déconnecté", self.event(host, "closed"))

    def test_protocol_version_mismatch_leaves_room_open(self):
        host = self.session("host", 0)
        port = self.event(host, "waiting")["port"]
        with socket.create_connection(("127.0.0.1", port), timeout=2) as sock:
            wrong = {"type": "hello", "version": VERSION + 1, "catalogue": self.catalogue.fingerprint}
            sock.sendall(json.dumps(wrong).encode() + b"\n")
            with sock.makefile("rb") as messages:
                response = json.loads(messages.readline())
            self.assertIn("incompatibles", response["value"])
        guest = self.session("join", port)
        self.assertEqual(self.event(guest, "state")["seat"], 2)

    def test_host_shutdown_notifies_guest_and_releases_port(self):
        host = self.session("host", 0)
        port = self.event(host, "waiting")["port"]
        guest = self.session("join", port)
        self.event(guest, "state")
        host.close()
        self.assertIn("perdue", self.event(guest, "closed"))
        self.event(self.session("host", port), "waiting")


if __name__ == "__main__":
    unittest.main()
