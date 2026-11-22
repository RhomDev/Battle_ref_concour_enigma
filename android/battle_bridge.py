import json
from pathlib import Path

from core.battle_session import BattleSession
from gameplay.partie import Catalogue


class BattleBridge:
    def __init__(self, data_root):
        data = Path(data_root)
        self.catalogue = Catalogue(data)
        self.session = None
        registry = json.loads((data / "medias.json").read_text(encoding="utf-8"))
        self.media = {}
        for item in registry:
            sources = ([item] if item["status"] == "demo_asset" else []) + item.get("localCopies", [])
            self.media[item["id"]] = [source["localPath"] for source in sources if source["kind"] == "image"]

    def cards(self):
        return json.dumps({
            card.id: {
                "name": card.name,
                "type": card.type,
                "cost": card.cost,
                "hp": getattr(card, "hp_max", None),
                "effect": getattr(card, "effect_type", None),
                "amount": getattr(card, "amount", None),
                "image": next(
                    (image for media_id in card.media for image in self.media.get(media_id, [])
                     if image.startswith("asset/image/catalogue/")),
                    None,
                ),
            }
            for card in self.catalogue.cards.values()
        })

    def start(self, mode, address):
        self.close()
        self.session = BattleSession(self.catalogue, mode, address)

    def poll(self):
        return json.dumps(self.session.poll() if self.session else [])

    def submit(self, action):
        if self.session:
            self.session.submit(json.loads(action))

    def close(self):
        if self.session:
            self.session.close()
            self.session = None
