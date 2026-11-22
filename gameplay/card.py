import json
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data"
CARD_KINDS = {"card_perso": "character", "card_ref": "ref"}


class Card_Item:
    def __init__(self, json_name, cat):
        folder = cat.rstrip("/")
        if folder not in CARD_KINDS:
            raise ValueError(f"Dossier de cartes invalide : {cat}")

        filename = Path(json_name)
        if len(filename.parts) != 1 or filename.suffix != ".json":
            raise ValueError(f"Nom de fiche invalide : {json_name}")
        path = DATA / folder / filename
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["kind"] != CARD_KINDS[folder]:
            raise ValueError(f"Type de carte incompatible avec le dossier : {path.name}")

        self.json_name = filename.name
        self.cat = folder
        self.type = data["kind"]
        self.id = data["id"]
        self.name = data["name"]
        self.cost = data["cost"]
        self.category = data["category"]
        self.text = data["text"]
        self.media = tuple(data["media"])

        if self.type == "character":
            self.hp_max = data["stats"]["hp"]
            self.hp = self.hp_max
            self.shield = 0
        else:
            effect = data["abilities"]["effect"]
            self.effect_type = effect["type"]
            self.amount = effect["amount"]
            self.synergy = data["synergy"]

    def to_dict(self):
        data = {
            "json_name": self.json_name,
            "cat": self.cat,
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "cost": self.cost,
            "category": self.category,
            "text": self.text,
            "media": list(self.media),
        }
        if self.type == "character":
            data.update({
                "hp": self.hp,
                "hp_max": self.hp_max,
                "shield": self.shield,
            })
        else:
            data.update({
                "effect_type": self.effect_type,
                "amount": self.amount,
                "synergy": self.synergy,
            })
        return data

    @classmethod
    def from_dict(cls, data):
        card = cls(data["json_name"], data["cat"])
        if card.type == "character":
            card.hp = data.get("hp", card.hp_max)
            card.hp_max = data.get("hp_max", card.hp_max)
            card.shield = data.get("shield", 0)
        else:
            card.effect_type = data.get("effect_type", card.effect_type)
            card.amount = data.get("amount", card.amount)
            card.synergy = data.get("synergy", card.synergy)
        return card

    def amount_with_synergy(self, deployed_character_ids):
        if self.synergy and self.synergy["character_id"] in deployed_character_ids:
            return self.amount + self.synergy["bonus"]
        return self.amount

    def take_damage(self, amount):
        amount = max(0, amount)
        absorbed = min(self.shield, amount)
        self.shield -= absorbed
        self.hp = max(0, self.hp - (amount - absorbed))
        return self.hp

    def heal(self, amount):
        self.hp = min(self.hp_max, self.hp + max(0, amount))

    def add_shield(self, amount):
        self.shield += max(0, amount)