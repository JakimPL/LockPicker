from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from lockpicker.tumbler.location import Location


class PickSet:
    def __init__(self, number_of_picks: int) -> None:
        self._number_of_picks = number_of_picks
        self._picks: Dict[int, Optional[Location]] = {pick: None for pick in range(number_of_picks)}
        self._current = 0

    @property
    def current(self) -> int:
        return self._current

    def select(self, pick: int) -> None:
        self._current = pick

    def change_current(self) -> None:
        self._current = (self._current + 1) % self._number_of_picks

    def get(self, pick: int) -> Optional[Location]:
        return self._picks.get(pick)

    def current_location(self) -> Optional[Location]:
        return self._picks[self._current]

    def set_current(self, location: Location) -> None:
        self._picks[self._current] = location

    def set(self, pick: int, location: Optional[Location]) -> None:
        self._picks[pick] = location

    def clear(self, pick: Optional[int] = None) -> None:
        target = self._current if pick is None else pick
        self._picks[target] = None

    def other_picks(self, location: Location) -> List[int]:
        return [
            pick for pick, loc in self._picks.items() if loc is not None and loc == location and pick != self._current
        ]

    def items(self) -> List[Tuple[int, Optional[Location]]]:
        return list(self._picks.items())
