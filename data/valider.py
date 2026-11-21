"""Valide les données et construit l'instantané HTML hors ligne."""
import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CARD_FOLDERS = {"character": "card_perso", "ref": "card_ref"}


def read(path):
    return json.loads((DATA / path).read_text(encoding="utf-8"))


def validate_and_index(values, schema_name):
    schema = read(f"schemas/{schema_name}.schema.json")
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    index = {}
    for entry in values:
        validator.validate(entry)
        if entry["id"] in index:
            raise ValueError(f"Identifiant répété dans {schema_name}: {entry['id']}")
        index[entry["id"]] = entry
    return index


def validate():
    fiches = sorted(path for folder in CARD_FOLDERS.values() for path in (DATA / folder).glob("*.json"))
    cards = [read(path) for path in fiches]
    media = read("medias.json")
    card_index = validate_and_index(cards, "carte")
    validate_and_index([read("template.json")], "carte")
    for path, card in zip(fiches, cards):
        if path.stem != card["id"] or path.parent.name != CARD_FOLDERS[card["kind"]]:
            raise ValueError(f"Nom ou dossier de fiche incompatible: {path.relative_to(DATA)}")
    cards.sort(key=lambda card: (card["kind"], card["cost"], card["id"]))
    media_index = validate_and_index(media, "media")
    for card in cards:
        synergy = card.get("synergy")
        if synergy is not None:
            partner_id = synergy["character_id"]
            partner = card_index.get(partner_id)
            if partner is None or partner["kind"] != "character":
                raise ValueError(f"Personnage associé invalide: {card['id']} / {partner_id}")
        for media_id in card["media"]:
            if media_id not in media_index:
                raise ValueError(f"Média inconnu: {media_id}")
    for item in media:
        if item["status"] == "demo_asset" and not (ROOT / item["localPath"]).is_file():
            raise ValueError(f"Fichier manquant: {item['localPath']}")
        for copy in item.get("localCopies", []):
            if not (ROOT / copy["localPath"]).is_file():
                raise ValueError(f"Copie locale manquante: {copy['localPath']}")
    return {"cards": cards, "media": media}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apercu", action="store_true", help="générer l’instantané JavaScript local")
    args = parser.parse_args()
    dataset = validate()
    if args.apercu:
        cards_json = json.dumps(dataset["cards"], ensure_ascii=False, indent=2)
        (DATA / "cartes.json").write_text(cards_json + "\n", encoding="utf-8")
        preview = ROOT / "apercu/catalogue.js"
        if preview.parent.is_dir():
            payload = json.dumps(dataset, ensure_ascii=False, separators=(",", ":"))
            preview.write_text(f"window.BATTLE_REF_PREVIEW = {payload};\n", encoding="utf-8")
    synergies = sum(card.get("synergy") is not None for card in dataset["cards"])
    print(f"{len(dataset['cards'])} cartes, {synergies} synergies et {len(dataset['media'])} entrées média validées.")
