from dataclasses import dataclass
from typing import Optional, Tuple

from lockpicker.tumbler.location import Location
from lockpicker.tumbler.state import TumblerState


@dataclass(frozen=True)
class State:
    current_pick: int
    tumblers: Tuple[Tuple[Location, TumblerState], ...]
    picks: Tuple[Tuple[int, Optional[Location]], ...]
