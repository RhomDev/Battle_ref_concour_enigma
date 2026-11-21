"""Valide les données et construit l'instantané HTML hors ligne."""
import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


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
    fiches = sorted((ROOT / "catalogue/fiches").glob("*.json"))
    cards = [read(path) for path in fiches]
    media = read("catalogue/medias.json")
    synergies = read("catalogue/synergies.json")
    card_index = validate_and_index(cards, "carte")
    cards.sort(key=lambda card: (card["kind"], card["cost"], card["id"]))
    media_index = validate_and_index(media, "media")
    validate_and_index(synergies, "synergie")
    for path in fiches:
        if path.stem != read(path)["id"]:
            raise ValueError(f"Nom de fiche incompatible: {path.name}")
    for card in cards:
        ability_ids = {ability["id"] for ability in card["abilities"]}
        if len(ability_ids) != len(card["abilities"]):
            raise ValueError(f"Capacité répétée: {card['id']}")
        for ability in card["abilities"]:
            targets = {effect["target"] for effect in ability["effects"]}
            if "chosen" in targets and ability["targeting"] == "none":
                raise ValueError(f"Capacité sans sélection: {card['id']} / {ability['id']}")
        for media_id in card["media"]:
            if media_id not in media_index:
                raise ValueError(f"Média inconnu: {media_id}")
    for item in media:
        if item["status"] == "demo_asset" and not (ROOT / item["localPath"]).is_file():
            raise ValueError(f"Fichier manquant: {item['localPath']}")
    amplified_refs = set()
    for synergy in synergies:
        source = card_index[synergy["sourceCardId"]]
        expected = "ref" if synergy["event"] == "ref_resolved" else "character"
        if source["kind"] != expected:
            raise ValueError(f"Événement incompatible: {synergy['id']}")
        if synergy.get("amplification"):
            if source["id"] in amplified_refs:
                raise ValueError(f"Amplification répétée: {source['id']}")
            amplified_refs.add(source["id"])
        for requirement in synergy["requirements"]:
            if card_index[requirement["cardId"]]["kind"] != "character":
                raise ValueError(f"Cible incompatible: {synergy['id']}")
            if synergy["event"] == "characters_combined" and requirement["cardId"] == source["id"]:
                raise ValueError(f"Combinaison de deux Personnages distincts attendue: {synergy['id']}")
            if requirement["kind"] == "chosen_card" and (
                expected != "ref" or source["abilities"][0]["targeting"] == "none"
            ):
                raise ValueError(f"Synergie sans sélection: {synergy['id']}")
        for effect in synergy["effects"]:
            target = effect["target"]
            if expected == "character" and effect["op"] == "damage":
                raise ValueError(f"Un Personnage ne peut pas infliger de dégâts: {synergy['id']}")
            if target == "chosen" and (expected != "ref" or source["abilities"][0]["targeting"] == "none"):
                raise ValueError(f"Effet sans sélection: {synergy['id']}")
            if ":" in target:
                side, card_id = target.split(":")
                if {"kind": "board_card", "cardId": card_id, "side": side} not in synergy["requirements"]:
                    raise ValueError(f"Cible de plateau sans condition: {synergy['id']}")
    if amplified_refs != {card["id"] for card in cards if card["kind"] == "ref"}:
        raise ValueError("Chaque Ref doit avoir une amplification.")
    return {"cards": cards, "media": media, "synergies": synergies}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apercu", action="store_true", help="générer l’instantané JavaScript local")
    args = parser.parse_args()
    dataset = validate()
    if args.apercu:
        cards_json = json.dumps(dataset["cards"], ensure_ascii=False, indent=2)
        (ROOT / "catalogue/cartes.json").write_text(cards_json + "\n")
        payload = json.dumps(dataset, ensure_ascii=False, separators=(",", ":"))
        (ROOT / "catalogue/apercu-data.js").write_text(f"window.BATTLE_REF_PREVIEW = {payload};\n")
    print(f"{len(dataset['cards'])} cartes, {len(dataset['synergies'])} synergies et {len(dataset['media'])} entrées média validées.")
