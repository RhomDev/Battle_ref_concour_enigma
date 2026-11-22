"""Lecteur GIF et MP3 commun à la collection et au plateau."""

from bisect import bisect_right

import pygame

from core.asset_manager import ROOT


class MediaPreview:
    def __init__(self, size):
        self.size = size
        self.channel = None
        self.frames = []
        self.frame_ends = []
        self.started_at = None

    def fit(self, surface):
        size = surface.get_rect().fit(pygame.Rect((0, 0), self.size)).size
        return pygame.transform.smoothscale(surface, (max(1, size[0]), max(1, size[1])))

    @property
    def frame(self):
        if self.started_at is None:
            return None
        elapsed = pygame.time.get_ticks() - self.started_at
        index = bisect_right(self.frame_ends, elapsed)
        return self.frames[index] if index < len(self.frames) else None

    @property
    def playing(self):
        return self.frame is not None or (self.channel is not None and self.channel.get_busy())

    def stop(self):
        if self.channel is not None:
            self.channel.stop()
            self.channel = None
        self.frames.clear()
        self.frame_ends.clear()
        self.started_at = None

    def update(self):
        if self.channel is not None and not self.channel.get_busy():
            self.channel = None
        if self.started_at is not None and self.frame is None:
            self.frames.clear()
            self.frame_ends.clear()
            self.started_at = None

    def play(self, animation, audio):
        self.stop()
        errors = []
        if animation:
            try:
                self._load_frames(animation)
            except (ImportError, OSError, ValueError, pygame.error):
                self.stop()
                errors.append("GIF indisponible.")
        if audio:
            try:
                if pygame.mixer.get_init() is None:
                    pygame.mixer.init()
                sound = pygame.mixer.Sound(ROOT / audio["localPath"])
                self.channel = sound.play(maxtime=audio["durationMs"])
                if self.channel is None:
                    errors.append("Sortie audio occupée.")
            except (OSError, pygame.error):
                errors.append("Son indisponible.")
        if self.frames:
            self.started_at = pygame.time.get_ticks()
        return " ".join(errors)

    def _load_frames(self, animation):
        from PIL import Image, ImageSequence

        limit = animation["durationMs"]
        elapsed = 0
        with Image.open(ROOT / animation["localPath"]) as image:
            for frame in ImageSequence.Iterator(image):
                rgba = frame.convert("RGBA")
                surface = pygame.image.frombytes(rgba.tobytes(), rgba.size, "RGBA")
                self.frames.append(self.fit(surface))
                elapsed += max(10, frame.info.get("duration") or 100)
                self.frame_ends.append(min(elapsed, limit))
                if elapsed >= limit:
                    break
