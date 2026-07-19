from typing import Dict, List, Optional

import pygame

from lockpicker.constants.config import settings
from lockpicker.tumbler.location import Location

SLIDE_CHANNELS = 12
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
