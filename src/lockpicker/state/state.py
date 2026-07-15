from dataclasses import dataclass
from typing import NamedTuple, Optional, Tuple

from lockpicker.tumbler.location import Location
from lockpicker.tumbler.state import TumblerState


class LocatedTumblerState(NamedTuple):
    location: Location
    tumbler_state: TumblerState


class PickState(NamedTuple):
    pick_index: int
    location: Optional[Location]


@dataclass(frozen=True)
class State:
    current_pick: int
    tumblers: Tuple[LocatedTumblerState, ...]
    picks: Tuple[PickState, ...]
