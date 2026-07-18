from __future__ import annotations

from typing import Dict, Iterator, Optional, Tuple

from lockpicker.constants.config import settings
from lockpicker.tumbler.location import Location


class LipEffects:
    def __init__(self) -> None:
        self._heights: Dict[Location, float] = {}
        self._glints: Dict[Location, int] = {}
        self._flourish: Optional[int] = None

    def observe(self, location: Location, height: float) -> None:
        previous = self._heights.get(location)
        if previous is not None and previous > 1.0 >= height:
            self._glints[location] = settings.theme.lip_glint_frames

        self._heights[location] = height

    def advance(self) -> None:
        self._glints = {location: count - 1 for location, count in self._glints.items() if count > 1}
        if self._flourish is not None and not self.flourish_finished:
            self._flourish += 1

    def reset(self) -> None:
        self._heights.clear()
        self._glints.clear()
        self._flourish = None

    def start_flourish(self) -> None:
        if self._flourish is None:
            self._flourish = 0

    def glints(self, *, upper: bool) -> Iterator[Tuple[int, float]]:
        for location, count in self._glints.items():
            if location.upper == upper:
                yield location.position, count / settings.theme.lip_glint_frames

    @property
    def flourish_strength(self) -> float:
        if self._flourish is None:
            return 0.0

        progress = min(self._flourish / settings.theme.win_flourish_frames, 1.0)
        return 1.0 - abs(2.0 * progress - 1.0)

    @property
    def flourish_finished(self) -> bool:
        return self._flourish is not None and self._flourish >= settings.theme.win_flourish_frames
