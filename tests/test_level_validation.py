from __future__ import annotations

from typing import Dict, List

import pytest
from pydantic import ValidationError

from lockpicker.level.level import Level
from lockpicker.level.validation import LevelSpec
from lockpicker.tumbler.definition import TumblerDefinition
from lockpicker.tumbler.location import Location
from lockpicker.tumbler.tumbler import Tumbler


def spec(
    *,
    position: int = 0,
    upper: bool = False,
    group: int = 0,
    height: int = 5,
    master: bool = True,
) -> Dict[str, object]:
    return {
        "position": position,
        "upper": upper,
        "group": group,
        "height": height,
        "post_release_height": 0,
        "master": master,
    }


def make_level(definitions: List[TumblerDefinition], max_height: int = 10) -> Level:
    tumblers = {definition.location: Tumbler(definition, max_height) for definition in definitions}
    return Level(1, max_height, tumblers, {})


def test_valid_level_spec_passes() -> None:
    LevelSpec(max_height=10, tumblers=[spec(position=0), spec(position=1, master=False)])


def test_negative_position_raises() -> None:
    with pytest.raises(ValidationError):
        LevelSpec(max_height=10, tumblers=[spec(position=-1)])


def test_zero_height_raises() -> None:
    with pytest.raises(ValidationError):
        LevelSpec(max_height=10, tumblers=[spec(height=0)])


def test_height_above_max_raises() -> None:
    with pytest.raises(ValidationError):
        LevelSpec(max_height=10, tumblers=[spec(height=11)])


def test_negative_group_raises() -> None:
    with pytest.raises(ValidationError):
        LevelSpec(max_height=10, tumblers=[spec(group=-1)])


def test_duplicate_group_location_raises() -> None:
    with pytest.raises(ValidationError):
        LevelSpec(max_height=10, tumblers=[spec(position=0), spec(position=0)])


def test_group_without_master_warns() -> None:
    with pytest.warns(UserWarning):
        LevelSpec(max_height=10, tumblers=[spec(master=False)])


def test_group_with_multiple_masters_warns() -> None:
    with pytest.warns(UserWarning):
        LevelSpec(max_height=10, tumblers=[spec(position=0), spec(position=1)])


def test_level_validate_wires_the_spec() -> None:
    make_level([TumblerDefinition(Location(0, False), 0, 5, 0, True)]).validate()


def test_level_validate_raises_on_out_of_range_height() -> None:
    level = make_level([TumblerDefinition(Location(0, False), 0, 99, 0, True)], max_height=10)
    with pytest.raises(ValidationError):
        level.validate()
