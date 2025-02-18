from dataclasses import dataclass

from lockpicker.location import Location


@dataclass(frozen=True)
class BaseTumbler:
    location: Location
    group: int
    height: int
    max_height: int
    post_release_height: int = 0
    master: bool = False
