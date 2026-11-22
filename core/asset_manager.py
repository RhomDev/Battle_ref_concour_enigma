import json
from functools import lru_cache
from pathlib import Path

import pygame


ROOT = Path(__file__).resolve().parents[1]
MEDIA_KINDS = ("image", "gif", "audio", "video")


class AssetManager:
    def __init__(self):
        registry = json.loads((ROOT / "data/medias.json").read_text(encoding="utf-8"))
        self.media = {item["id"]: item for item in registry}

    def media_for(self, media_ids):
        items = [self.media[media_id] for media_id in media_ids]
        demos = [item for item in items if item["status"] == "demo_asset"]
        originals = [
            {**copy, "sourceUrl": item["sourceUrl"]}
            for item in items
            for copy in item.get("localCopies", [])
        ]

        media = {}
        for kind in MEDIA_KINDS:
            sources = demos + originals if kind in ("image", "gif") else originals + demos
            media[kind] = next((item for item in sources if item["kind"] == kind), None)
        return media

    @lru_cache(maxsize=32)
    def load_image(self, local_path):
        image = pygame.image.load(ROOT / local_path)
        if pygame.display.get_surface() is not None:
            return image.convert_alpha()
        return image
