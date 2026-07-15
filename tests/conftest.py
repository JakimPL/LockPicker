from __future__ import annotations

import os
from typing import Callable, Dict, Iterable, Optional

import pytest

from lockpicker.engine.lock import Lock
from lockpicker.level.level import Level
from lockpicker.tumbler.definition import TumblerDefinition
from lockpicker.tumbler.location import Location
from lockpicker.tumbler.tumbler import Tumbler

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

TumblerFactory = Callable[..., Tumbler]
LevelFactory = Callable[..., Level]
LockFactory = Callable[..., Lock]


@pytest.fixture
def build_tumbler() -> TumblerFactory:
    def _build(
        *,
        position: int = 0,
        upper: bool = False,
        group: int = 0,
        height: int = 5,
        max_height: int = 10,
        post_release_height: int = 0,
        master: bool = False,
    ) -> Tumbler:
        definition = TumblerDefinition(Location(position, upper), group, height, post_release_height, master)
        return Tumbler(definition, max_height)

    return _build


@pytest.fixture
def build_level() -> LevelFactory:
    def _build(
        definitions: Iterable[TumblerDefinition],
        *,
        number_of_picks: int = 1,
        max_height: int = 10,
        bindings: Optional[Dict[Location, Dict[Location, int]]] = None,
    ) -> Level:
        tumblers = {definition.location: Tumbler(definition, max_height) for definition in definitions}
        return Level(number_of_picks, max_height, tumblers, bindings or {})

    return _build


@pytest.fixture
def build_lock(build_level: LevelFactory) -> LockFactory:
    def _build(
        definitions: Iterable[TumblerDefinition],
        *,
        number_of_picks: int = 1,
        max_height: int = 10,
        bindings: Optional[Dict[Location, Dict[Location, int]]] = None,
    ) -> Lock:
        level = build_level(
            definitions,
            number_of_picks=number_of_picks,
            max_height=max_height,
            bindings=bindings,
        )
        return Lock(level)

    return _build
