from dataclasses import dataclass
from typing import Dict, Optional

from lockpicker.tumbler.location import Location


@dataclass(frozen=True)
class Snapshot:
    heights: Dict[Location, int]
    picks: Dict[int, Optional[Location]]
