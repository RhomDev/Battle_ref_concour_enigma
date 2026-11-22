"""Gestionnaire audio pour Battle Ref Arena.

Charge et joue des sons identifiés par un nom court.
Repose sur pygame.mixer ; compatible avec l'AssetManager existant.

Usage :
    from core.sound_manager import SoundManager
    sounds = SoundManager()
    sounds.play("sda_you_shall_not_pass")
    sounds.set_volume(0.8)
"""

import json
import logging
from pathlib import Path
from random import SystemRandom

import pygame

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "asset" / "sound" / "sounds.json"
BATTLE_TRACKS = (
    "battle-bossfight.ogg",
    "battle-final.ogg",
    "battle-ghosts-and-heroes.ogg",
    "battle-hard-boss.ogg",
)
BATTLE_MUSIC_VOLUME = 0.22
BATTLE_MUSIC_DUCKED_VOLUME = 0.07

logger = logging.getLogger(__name__)


class SoundManager:
    """Charge et joue des sons par identifiant.

    Les fichiers sont mis en cache après le premier chargement.
    Le mixer Pygame doit avoir été initialisé avant d'appeler play().
    """

    def __init__(self, registry_path: Path = REGISTRY_PATH):
        self._registry: dict = {}
        self._cache: dict[str, pygame.mixer.Sound] = {}
        self._volume: float = 1.0
        self._battle_music_ducked = False

        if registry_path.exists():
            try:
                self._registry = json.loads(registry_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("SoundManager : impossible de lire le registre : %s", exc)

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def play(self, sound_id: str) -> pygame.mixer.Channel | None:
        """Joue le son identifié et retourne le Channel Pygame, ou None en cas d'erreur."""
        sound = self._load(sound_id)
        if sound is None:
            return None
        try:
            channel = sound.play()
            return channel
        except pygame.error as exc:
            logger.warning("SoundManager.play(%s) : %s", sound_id, exc)
            return None

    def play_with_duration(self, sound_id: str) -> pygame.mixer.Channel | None:
        """Joue le son en respectant la durée définie dans le registre."""
        sound = self._load(sound_id)
        if sound is None:
            return None
        entry = self._registry.get(sound_id, {})
        duration_ms = int(entry.get("duration_s", 0) * 1000) or -1
        try:
            channel = sound.play(maxtime=duration_ms if duration_ms > 0 else 0)
            return channel
        except pygame.error as exc:
            logger.warning("SoundManager.play_with_duration(%s) : %s", sound_id, exc)
            return None

    def set_volume(self, volume: float) -> None:
        """Ajuste le volume global (0.0–1.0) pour tous les sons chargés."""
        self._volume = max(0.0, min(1.0, volume))
        for sound in self._cache.values():
            sound.set_volume(self._volume)

    def get_volume(self) -> float:
        return self._volume

    def play_battle_music(self) -> None:
        """Choisit une piste de combat et la joue en boucle."""
        if not self._ensure_mixer():
            return

        track = SystemRandom().choice(BATTLE_TRACKS)
        path = REGISTRY_PATH.parent / track
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(BATTLE_MUSIC_VOLUME)
            pygame.mixer.music.play(loops=-1)
            self._battle_music_ducked = False
        except (pygame.error, OSError) as exc:
            logger.warning("Musique de combat indisponible (%s) : %s", track, exc)

    def set_battle_music_ducked(self, ducked: bool) -> None:
        """Baisse la musique pendant la lecture d'un extrait de Réf."""
        if ducked == self._battle_music_ducked or not pygame.mixer.get_init():
            return
        if pygame.mixer.music.get_busy():
            volume = BATTLE_MUSIC_DUCKED_VOLUME if ducked else BATTLE_MUSIC_VOLUME
            pygame.mixer.music.set_volume(volume)
            self._battle_music_ducked = ducked

    def stop_battle_music(self) -> None:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()

    def preload(self, *sound_ids: str) -> None:
        """Précharge les sons dans le cache sans les jouer."""
        for sid in sound_ids:
            self._load(sid)

    def stop_all(self) -> None:
        """Arrête tous les canaux audio."""
        pygame.mixer.stop()

    def available_ids(self) -> list[str]:
        """Retourne la liste des identifiants connus dans le registre."""
        return list(self._registry.keys())

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _ensure_mixer(self) -> bool:
        """Initialise pygame.mixer si nécessaire. Retourne True si opérationnel."""
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except pygame.error as exc:
                logger.error("SoundManager : impossible d'initialiser le mixer : %s", exc)
                return False
        return True

    def _load(self, sound_id: str) -> pygame.mixer.Sound | None:
        """Charge un son depuis le cache ou le disque."""
        if sound_id in self._cache:
            return self._cache[sound_id]

        entry = self._registry.get(sound_id)
        if entry is None:
            logger.warning("SoundManager : identifiant inconnu '%s'", sound_id)
            return None

        if not self._ensure_mixer():
            return None

        path = ROOT / entry["file"]
        if not path.exists():
            logger.warning("SoundManager : fichier introuvable : %s", path)
            return None

        try:
            sound = pygame.mixer.Sound(str(path))
            sound.set_volume(self._volume)
            self._cache[sound_id] = sound
            return sound
        except (pygame.error, OSError) as exc:
            logger.warning("SoundManager : chargement échoué pour '%s' : %s", sound_id, exc)
            return None
