from typing import Dict, Optional

import pygame

from lockpicker.constants.config import settings
from lockpicker.engine.events import Sound
from lockpicker.game.audio.slides import SLIDE_CHANNELS, SlidePlayer
from lockpicker.paths import SOUNDS_DIR
from lockpicker.tumbler.location import Location

FILES: Dict[Sound, str] = {
    Sound.PUSH: "tumbler_push.wav",
    Sound.SET: "tumbler_set.wav",
    Sound.JAM: "jam.wav",
    Sound.BREAK: "pick_break.wav",
}

ONESHOT_CHANNELS = 8


class SoundBoard:
    def __init__(self) -> None:
        self._sounds: Dict[Sound, pygame.mixer.Sound] = {}
        self._slides: Optional[SlidePlayer] = None
        self._enabled = settings.audio.enabled and self._ensure_mixer()
        if self._enabled:
            self._configure_channels()
            self._load()
            self._create_slides()

    def play(self, sound: Sound) -> None:
        clip = self._sounds.get(sound)
        if clip is not None:
            clip.play()

    def observe_motion(self, location: Location, height: float) -> None:
        if self._slides is not None:
            self._slides.observe(location, height)

    def silence_slides(self) -> None:
        if self._slides is not None:
            self._slides.silence()

    def _create_slides(self) -> None:
        clip = self._sounds.get(Sound.PUSH)
        if clip is not None:
            self._slides = SlidePlayer(clip)

    def _configure_channels(self) -> None:
        pygame.mixer.set_num_channels(SLIDE_CHANNELS + ONESHOT_CHANNELS)
        pygame.mixer.set_reserved(SLIDE_CHANNELS)

    def _load(self) -> None:
        volume = settings.audio.volume
        for sound, filename in FILES.items():
            path = SOUNDS_DIR / filename
            if not path.exists():
                continue

            clip = pygame.mixer.Sound(str(path))
            clip.set_volume(volume)
            self._sounds[sound] = clip

    @staticmethod
    def _ensure_mixer() -> bool:
        if pygame.mixer.get_init() is not None:
            return True

        try:
            pygame.mixer.init()
        except pygame.error:
            return False

        return pygame.mixer.get_init() is not None
