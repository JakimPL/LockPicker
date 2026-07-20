from __future__ import annotations

from typing import List

from lockpicker.constants.config import settings
from lockpicker.game.effects import LipEffects
from lockpicker.tumbler.location import Location

UPPER = Location(0, True)
LOWER = Location(1, False)


def glint_positions(effects: LipEffects, *, upper: bool) -> List[int]:
    return [position for position, _ in effects.glints(upper=upper)]


def test_crossing_fires_glint_once() -> None:
    effects = LipEffects()
    effects.observe(UPPER, 2.0)
    effects.observe(UPPER, 1.5)
    assert not glint_positions(effects, upper=True)

    effects.observe(UPPER, 1.0)
    assert list(effects.glints(upper=True)) == [(0, 1.0)]
    assert not glint_positions(effects, upper=False)

    effects.observe(UPPER, 1.0)
    effects.observe(UPPER, 0.5)
    assert len(glint_positions(effects, upper=True)) == 1


def test_starting_seated_fires_nothing() -> None:
    effects = LipEffects()
    effects.observe(UPPER, 1.0)
    effects.observe(LOWER, 0.5)
    assert not glint_positions(effects, upper=True)
    assert not glint_positions(effects, upper=False)


def test_glint_decays_over_configured_frames() -> None:
    effects = LipEffects()
    effects.observe(LOWER, 2.0)
    effects.observe(LOWER, 1.0)

    strengths = []
    for _ in range(settings.theme.lip_glint_frames):
        strengths.append(next(effects.glints(upper=False))[1])
        effects.advance()

    assert not glint_positions(effects, upper=False)
    assert strengths[0] == 1.0
    assert all(first > second for first, second in zip(strengths, strengths[1:]))


def test_reset_clears_memory() -> None:
    effects = LipEffects()
    effects.observe(UPPER, 2.0)
    effects.observe(UPPER, 1.0)
    effects.start_flourish()
    effects.reset()

    assert not glint_positions(effects, upper=True)
    assert effects.flourish_strength == 0.0
    assert not effects.flourish_finished

    effects.observe(UPPER, 1.0)
    assert not glint_positions(effects, upper=True)


def test_flourish_rises_falls_and_finishes() -> None:
    effects = LipEffects()
    assert effects.flourish_strength == 0.0
    assert not effects.flourish_finished

    effects.start_flourish()
    strengths = [effects.flourish_strength]
    for _ in range(settings.theme.win_flourish_frames):
        assert not effects.flourish_finished
        effects.advance()
        strengths.append(effects.flourish_strength)

    assert effects.flourish_finished
    assert strengths[0] == 0.0
    assert strengths[-1] == 0.0
    peak = strengths.index(max(strengths))
    assert 0 < peak < len(strengths) - 1
    assert max(strengths) > 0.9


def test_start_flourish_is_idempotent() -> None:
    effects = LipEffects()
    effects.start_flourish()
    for _ in range(3):
        effects.advance()

    strength = effects.flourish_strength
    effects.start_flourish()
    assert effects.flourish_strength == strength
