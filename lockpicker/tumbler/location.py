from typing import NamedTuple


class Location(NamedTuple):
    position: int
    upper: bool

    @property
    def counter(self) -> "Location":
        return Location(self.position, not self.upper)
