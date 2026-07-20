from __future__ import annotations

from typing import Dict, Optional

from lockpicker.constants.config import settings
from lockpicker.game.animation import Animation, HeightChange, PickChange, compute_animation_steps
from lockpicker.state.snapshot import Snapshot
from lockpicker.tumbler.location import Location
from tests.conftest import TumblerFactory

A = Location(0, False)
B = Location(1, False)


def snapshot(heights: Dict[Location, int], picks: Optional[Dict[int, Optional[Location]]] = None) -> Snapshot:
    return Snapshot(dict(heights), dict(picks) if picks is not None else {0: None})


def test_load_activates_first_step() -> None:
    animation = Animation()
    animation.load(compute_animation_steps([snapshot({A: 5}), snapshot({A: 3}), snapshot({A: 1})]))

    assert animation.current_item is not None
    assert animation.current_item.tumblers[A] == HeightChange(5, 3)
    assert animation.value == 0.0


def test_height_starts_at_step_start(build_tumbler: TumblerFactory) -> None:
    tumbler = build_tumbler(height=1)
    animation = Animation()
    animation.load(compute_animation_steps([snapshot({A: 5}), snapshot({A: 1})]))

    assert animation.height(tumbler) == 5.0


def test_no_change_steps_are_filtered() -> None:
    steps = compute_animation_steps([snapshot({A: 5}), snapshot({A: 5}), snapshot({A: 2})])

    assert len(steps) == 1
    assert steps[0].tumblers[A] == HeightChange(5, 2)


def test_steps_keep_unchanged_entries() -> None:
    steps = compute_animation_steps([snapshot({A: 5, B: 4}), snapshot({A: 5, B: 2})])

    assert steps[0].tumblers[A] == HeightChange(5, 5)
    assert steps[0].picks[0] == PickChange(None, None)


def test_changes_share_progress(build_tumbler: TumblerFactory) -> None:
    slow = build_tumbler(position=0, height=1)
    fast = build_tumbler(position=1, height=1)
    animation = Animation()
    animation.load(compute_animation_steps([snapshot({A: 5, B: 2}), snapshot({A: 1, B: 1})]))
    animation.value = 2.0

    assert animation.progress == 0.5
    assert animation.height(slow) == 3.0
    assert animation.height(fast) == 1.5


def test_steps_play_in_order() -> None:
    animation = Animation()
    animation.load(compute_animation_steps([snapshot({A: 5}), snapshot({A: 3}), snapshot({A: 1})]))
    animation.value = 10.0
    animation.advance()

    assert animation.current_item is not None
    assert animation.current_item.tumblers[A] == HeightChange(3, 1)


def test_pick_move_uses_travel_span() -> None:
    animation = Animation()
    animation.load(compute_animation_steps([snapshot({A: 5}, {0: None}), snapshot({A: 5}, {0: A})]))

    assert animation.pick_change(0) == PickChange(None, A)
    animation.value = settings.animation.pick_travel / 2
    assert animation.progress == 0.5

    animation.reset()
    assert animation.pick_change(0) is None


def test_advance_completes_pick_step() -> None:
    animation = Animation()
    animation.load(compute_animation_steps([snapshot({A: 5}, {0: None}), snapshot({A: 5}, {0: A})]))

    frames = 0
    while animation.advance():
        frames += 1
        assert frames < 10_000

    assert animation.active is False
