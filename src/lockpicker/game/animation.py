from __future__ import annotations

from typing import Dict, List, NamedTuple, TypeAlias

from lockpicker.tumbler.location import Location


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
