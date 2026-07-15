from __future__ import annotations

from dataclasses import dataclass

from lockpicker.tumbler.location import Location


@dataclass(frozen=True)
class TumblerDefinition:
    location: Location
    group: int
    height: int
    post_release_height: int = 0
    master: bool = False
