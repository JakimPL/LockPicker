from __future__ import annotations

from typing import Dict, List, Optional

import pygame

from lockpicker.constants.config import settings
from lockpicker.engine.events import Sound
from lockpicker.paths import SOUNDS_DIR
from lockpicker.tumbler.location import Location

FILES: Dict[Sound, str] = {
    Sound.PUSH: "tumbler_push.wav",
    Sound.SET: "tumbler_set.wav",
    Sound.JAM: "jam.wav",
    Sound.BREAK: "pick_break.wav",
}

SLIDE_CHANNELS = 12
ONESHOT_CHANNELS = 8
SLIDE_GAIN = 0.9


class SlidePlayer:
    def __init__(self, clip: pygame.mixer.Sound) -> None:
        self._clip = clip
        self._speed_reference = settings.animation.speed * 1.5
        self._silence_speed = self._speed_reference * 0.05
        self._free: List[int] = list(range(SLIDE_CHANNELS))
        self._voices: Dict[Location, int] = {}
        self._heights: Dict[Location, float] = {}

    def observe(self, location: Location, height: float) -> None:
        previous = self._heights.get(location)
        self._heights[location] = height
        if previous is not None:
            self._drive(location, abs(height - previous))

    def silence(self) -> None:
        for location in list(self._voices):
            self._release(location)

        self._heights.clear()

    def _drive(self, location: Location, speed: float) -> None:
        if speed <= self._silence_speed:
            self._release(location)
            return

        volume = min(1.0, speed / self._speed_reference) * SLIDE_GAIN
        index = self._voices.get(location)
        if index is None:
            index = self._acquire(location)
            if index is None:
                return

            channel = pygame.mixer.Channel(index)
            channel.set_volume(volume)
            channel.play(self._clip, loops=-1)
        else:
            pygame.mixer.Channel(index).set_volume(volume)

    def _acquire(self, location: Location) -> Optional[int]:
        if not self._free:
            return None

        index = self._free.pop()
        self._voices[location] = index
        return index

    def _release(self, location: Location) -> None:
        index = self._voices.pop(location, None)
        if index is not None:
            pygame.mixer.Channel(index).stop()
            self._free.append(index)


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
