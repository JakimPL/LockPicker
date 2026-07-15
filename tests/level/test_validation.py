from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import msgpack
import pytest
from pydantic import ValidationError

from lockpicker.level.level import Level
from lockpicker.level.validation import LevelSpec
from lockpicker.tumbler.definition import TumblerDefinition
from lockpicker.tumbler.location import Location
from tests.conftest import LevelFactory


def tumbler_spec(
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


@dataclass(frozen=True)
class SpecCase:
    case_id: str
    tumblers: List[Dict[str, object]]
    number_of_picks: int = 1
    max_height: int = 10


INVALID_SPEC_CASES = [
    SpecCase("negative_position", [tumbler_spec(position=-1)]),
    SpecCase("zero_height", [tumbler_spec(height=0)]),
    SpecCase("height_above_max", [tumbler_spec(height=11)]),
    SpecCase("negative_group", [tumbler_spec(group=-1)]),
    SpecCase("duplicate_location", [tumbler_spec(position=0), tumbler_spec(position=0)]),
    SpecCase("non_positive_number_of_picks", [], number_of_picks=0),
    SpecCase("non_positive_max_height", [], max_height=0),
]

WARNING_SPEC_CASES = [
    SpecCase("group_without_master", [tumbler_spec(master=False)]),
    SpecCase("multiple_masters", [tumbler_spec(position=0), tumbler_spec(position=1)]),
]


def test_valid_level_spec_passes() -> None:
    LevelSpec(
        number_of_picks=1,
        max_height=10,
        tumblers=[tumbler_spec(position=0), tumbler_spec(position=1, master=False)],
    )


@pytest.mark.parametrize("case", INVALID_SPEC_CASES, ids=[case.case_id for case in INVALID_SPEC_CASES])
def test_invalid_level_spec_raises(case: SpecCase) -> None:
    with pytest.raises(ValidationError):
        LevelSpec(number_of_picks=case.number_of_picks, max_height=case.max_height, tumblers=case.tumblers)


@pytest.mark.parametrize("case", WARNING_SPEC_CASES, ids=[case.case_id for case in WARNING_SPEC_CASES])
def test_level_spec_warns_on_master_imbalance(case: SpecCase) -> None:
    with pytest.warns(UserWarning):
        LevelSpec(number_of_picks=case.number_of_picks, max_height=case.max_height, tumblers=case.tumblers)


def test_level_validate_wires_the_spec(build_level: LevelFactory) -> None:
    level = build_level([TumblerDefinition(Location(0, False), 0, 5, 0, True)])
    level.validate()


def test_level_validate_raises_on_out_of_range_height(build_level: LevelFactory) -> None:
    level = build_level([TumblerDefinition(Location(0, False), 0, 99, 0, True)], max_height=10)
    with pytest.raises(ValidationError):
        level.validate()


def test_deserialize_rejects_non_positive_number_of_picks() -> None:
    data = msgpack.packb({"number_of_picks": 0, "max_height": 10, "tumblers": [], "bindings": []})
    with pytest.raises(ValidationError):
        Level.deserialize(data)
