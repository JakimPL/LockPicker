from __future__ import annotations

import pytest

from lockpicker.tumbler.definition import TumblerDefinition
from lockpicker.tumbler.location import Location
from lockpicker.tumbler.tumbler import Tumbler


def make_tumbler(
    height: int = 5,
    max_height: int = 10,
    position: int = 0,
    upper: bool = False,
    group: int = 0,
    post_release_height: int = 0,
    master: bool = False,
) -> Tumbler:
    definition = TumblerDefinition(Location(position, upper), group, height, post_release_height, master)
    return Tumbler(definition, max_height)


def test_construction_exposes_definition_fields() -> None:
    tumbler = make_tumbler(height=5, group=2, post_release_height=1, master=True)
    assert tumbler.base_height == 5
    assert tumbler.height == 5
    assert tumbler.group == 2
    assert tumbler.post_release_height == 1
    assert tumbler.master is True
    assert tumbler.pushed is False
    assert tumbler.jammed is False


def test_free_tracks_current_height() -> None:
    assert make_tumbler(height=1).free is True
    assert make_tumbler(height=2).free is False


def test_push_collapses_to_one() -> None:
    tumbler = make_tumbler(height=6)
    tumbler.push()
    assert tumbler.pushed is True
    assert tumbler.height == 1
    assert tumbler.free is True


def test_jam_then_unjam() -> None:
    tumbler = make_tumbler()
    tumbler.jam()
    assert tumbler.jammed is True
    assert tumbler.pushed is True
    tumbler.unjam()
    assert tumbler.jammed is False


def test_direct_release_resets_difference_and_adds_post_release_height() -> None:
    tumbler = make_tumbler(height=5, post_release_height=2, max_height=20)
    tumbler.set_difference(3)
    tumbler.release(direct=True)
    assert tumbler.difference == 0
    assert tumbler.height == 7


def test_set_height_reauthors_and_recalculates() -> None:
    tumbler = make_tumbler(height=5)
    tumbler.set_height(8)
    assert tumbler.base_height == 8
    assert tumbler.height == 8


@pytest.mark.parametrize("height", [0, -1, 11])
def test_set_height_rejects_out_of_bounds(height: int) -> None:
    tumbler = make_tumbler(height=5, max_height=10)
    with pytest.raises(ValueError):
        tumbler.set_height(height)


def test_set_group_rejects_negative() -> None:
    tumbler = make_tumbler()
    with pytest.raises(ValueError):
        tumbler.set_group(-1)


def test_set_group_and_master_authoring() -> None:
    tumbler = make_tumbler(group=0, master=False)
    tumbler.set_group(3)
    tumbler.set_master(True)
    assert tumbler.group == 3
    assert tumbler.master is True


def test_set_difference_respects_recalculate_flag() -> None:
    tumbler = make_tumbler(height=5, max_height=20)
    tumbler.set_difference(3)
    assert tumbler.height == 8
    tumbler.set_difference(0, recalculate=False)
    assert tumbler.difference == 0
    assert tumbler.height == 8


def test_counter_clamps_available_height() -> None:
    tumbler = make_tumbler(height=8, max_height=10)
    counter = make_tumbler(height=5, max_height=10, upper=True)
    tumbler.set_counter(counter)
    assert tumbler.height == 5
    tumbler.set_counter(None)
    assert tumbler.height == 8


def test_copy_is_independent() -> None:
    tumbler = make_tumbler(height=5)
    clone = tumbler.copy()
    clone.set_height(9)
    assert tumbler.base_height == 5
    assert clone.base_height == 9
