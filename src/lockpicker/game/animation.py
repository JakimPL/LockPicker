from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, NamedTuple, TypeAlias

from lockpicker.constants.config import settings
from lockpicker.tumbler.location import Location

if TYPE_CHECKING:
    from lockpicker.tumbler.tumbler import Tumbler


class HeightChange(NamedTuple):
    start: int
    end: int


AnimationStep: TypeAlias = Dict[Location, HeightChange]


def compute_animation_steps(snapshots: List[Dict[Location, int]]) -> List[AnimationStep]:
    steps: List[AnimationStep] = []
    for current, following in zip(snapshots, snapshots[1:]):
        step: AnimationStep = {
            location: HeightChange(height, following.get(location, height)) for location, height in current.items()
        }
        if step:
            steps.append(step)

    return list(reversed(steps))


class Animation:
    def __init__(self) -> None:
        self.value = 0.0
        self.items: List[AnimationStep] = []
        self.current_item: AnimationStep = {}

    @property
    def active(self) -> bool:
        return bool(self.items or self.current_item)

    def load(self, steps: List[AnimationStep]) -> None:
        self.items = steps

    def reset(self) -> None:
        self.value = 0.0
        self.items = []
        self.current_item = {}

    def advance(self) -> bool:
        if not self.active:
            return False

        self.value += settings.animation.speed
        if self.current_item and self.value >= self._max_value():
            self.current_item = {}

        if self.items and not self.current_item:
            self.current_item = self.items.pop()
            self.value = 0.0

        return True

    def _max_value(self) -> int:
        return max(abs(change.end - change.start) for change in self.current_item.values())

    def _eased_value(self) -> float:
        span = self._max_value()
        if span == 0:
            return self.value

        progress = min(self.value / span, 1.0)
        return span * progress * progress * (3.0 - 2.0 * progress)

    def height(self, tumbler: Tumbler) -> float:
        change = self.current_item.get(tumbler.location)
        if change is None:
            return tumbler.height

        value = self._eased_value()
        if change.end > change.start:
            return change.start + min(value, change.end - change.start)

        return change.start + max(-value, change.end - change.start)
