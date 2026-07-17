from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, NamedTuple, Optional

from lockpicker.constants.config import settings
from lockpicker.state.snapshot import Snapshot
from lockpicker.tumbler.location import Location

if TYPE_CHECKING:
    from lockpicker.tumbler.tumbler import Tumbler


class HeightChange(NamedTuple):
    start: int
    end: int


class PickChange(NamedTuple):
    start: Optional[Location]
    end: Optional[Location]


class AnimationStep(NamedTuple):
    tumblers: Dict[Location, HeightChange]
    picks: Dict[int, PickChange]


def compute_animation_steps(snapshots: List[Snapshot]) -> List[AnimationStep]:
    steps: List[AnimationStep] = []
    for current, following in zip(snapshots, snapshots[1:]):
        tumblers = {
            location: HeightChange(height, following.heights.get(location, height))
            for location, height in current.heights.items()
        }
        picks = {
            pick: PickChange(location, following.picks.get(pick, location)) for pick, location in current.picks.items()
        }
        step = AnimationStep(tumblers, picks)
        if _step_changes(step):
            steps.append(step)

    return list(reversed(steps))


def _step_changes(step: AnimationStep) -> bool:
    changes = list(step.tumblers.values()) + list(step.picks.values())
    return any(change.start != change.end for change in changes)


class Animation:
    def __init__(self) -> None:
        self.value = 0.0
        self.items: List[AnimationStep] = []
        self.current_item: Optional[AnimationStep] = None

    @property
    def active(self) -> bool:
        return bool(self.items) or self.current_item is not None

    def load(self, steps: List[AnimationStep]) -> None:
        self.items = steps
        self.value = 0.0
        self.current_item = self.items.pop() if self.items else None

    def reset(self) -> None:
        self.value = 0.0
        self.items = []
        self.current_item = None

    def advance(self) -> bool:
        if not self.active:
            return False

        self.value += settings.animation.speed
        if self.current_item is not None and self.value >= self._span(self.current_item):
            self.current_item = None

        if self.items and self.current_item is None:
            self.current_item = self.items.pop()
            self.value = 0.0

        return True

    @property
    def progress(self) -> float:
        if self.current_item is None:
            return 1.0

        span = self._span(self.current_item)
        if span <= 0.0:
            return 1.0

        ratio = min(self.value / span, 1.0)
        return ratio * ratio * (3.0 - 2.0 * ratio)

    def height(self, tumbler: Tumbler) -> float:
        if self.current_item is None:
            return tumbler.height

        change = self.current_item.tumblers.get(tumbler.location)
        if change is None:
            return tumbler.height

        return change.start + (change.end - change.start) * self.progress

    def pick_change(self, pick: int) -> Optional[PickChange]:
        if self.current_item is None:
            return None

        return self.current_item.picks.get(pick)

    @staticmethod
    def _span(step: AnimationStep) -> float:
        span = float(max((abs(change.end - change.start) for change in step.tumblers.values()), default=0))
        if any(change.start != change.end for change in step.picks.values()):
            span = max(span, settings.animation.pick_travel)

        return span
