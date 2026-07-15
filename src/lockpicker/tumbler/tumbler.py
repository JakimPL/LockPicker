from __future__ import annotations

from dataclasses import replace
from typing import Optional

from lockpicker.tumbler.definition import TumblerDefinition
from lockpicker.tumbler.location import Location
from lockpicker.tumbler.state import TumblerState


class Tumbler:
    def __init__(
        self,
        definition: TumblerDefinition,
        max_height: int,
        state: Optional[TumblerState] = None,
        counter: Optional[Tumbler] = None,
    ):
        self._definition = definition
        self._max_height = max_height
        self._state = TumblerState(definition.height) if state is None else state
        self._counter = counter

    def __repr__(self) -> str:
        return (
            f"Tumbler(location={self.location}, group={self.group}, height={self.base_height}, "
            f"max_height={self.max_height}, post_release_height={self.post_release_height}, master={self.master}, "
            f"current_height={self._state.current_height}, pushed={self._state.pushed}, "
            f"jammed={self._state.jammed}, release={self._state.release}, difference={self._state.difference})"
        )

    def copy(self) -> Tumbler:
        return Tumbler(
            self._definition,
            self._max_height,
            self._state.copy(),
            self._counter,
        )

    def jam(self) -> None:
        self._state.release = False
        self._state.jammed = True
        self._state.pushed = True

    def push(self) -> None:
        self._state.release = False
        self._state.pushed = True
        self._recalculate_current_height()

    def unjam(self) -> None:
        self._state.release = False
        self._state.jammed = False

    def release(self, direct: bool = False) -> None:
        self._state.jammed = False
        self._state.pushed = False
        self._state.release = direct
        if direct:
            self._state.difference = 0

        self._recalculate_current_height()

    @property
    def pushed(self) -> bool:
        return self._state.pushed

    @property
    def jammed(self) -> bool:
        return self._state.jammed

    @property
    def height(self) -> int:
        return self._state.current_height

    def _recalculate_current_height(self) -> None:
        if self.pushed:
            height = 1
        else:
            height = self.base_height + self.difference
            if self._state.release:
                height += self.post_release_height

        counter_height = self._counter.height if self._counter is not None else 0
        self._state.current_height = max(1, min(height, self._max_height - counter_height))

    @property
    def base_height(self) -> int:
        return self._definition.height

    def set_height(self, height: int) -> None:
        if height < 1:
            raise ValueError(f"Height must be at least 1, got {height}")

        if height > self._max_height:
            raise ValueError(f"Height must be at most {self._max_height}, got {height}")

        self._definition = replace(self._definition, height=height)
        self._recalculate_current_height()

    @property
    def definition(self) -> TumblerDefinition:
        return self._definition

    @property
    def location(self) -> Location:
        return self._definition.location

    @property
    def position(self) -> int:
        return self._definition.location.position

    @property
    def upper(self) -> bool:
        return self._definition.location.upper

    @property
    def group(self) -> int:
        return self._definition.group

    def set_group(self, group: int) -> None:
        if group < 0:
            raise ValueError(f"Group must be non-negative, got {group}")

        self._definition = replace(self._definition, group=group)

    @property
    def master(self) -> bool:
        return self._definition.master

    def set_master(self, master: bool) -> None:
        self._definition = replace(self._definition, master=master)

    @property
    def post_release_height(self) -> int:
        return self._definition.post_release_height

    def set_post_release_height(self, height: int) -> None:
        self._definition = replace(self._definition, post_release_height=height)

    @property
    def difference(self) -> int:
        return self._state.difference

    def set_difference(self, difference: int, *, recalculate: bool = True) -> None:
        self._state.difference = difference
        if recalculate:
            self._recalculate_current_height()

    @property
    def max_height(self) -> int:
        return self._max_height

    def set_counter(self, counter: Optional[Tumbler]) -> None:
        self._counter = counter
        self._recalculate_current_height()

    @property
    def free(self) -> bool:
        return self.height <= 1

    @property
    def state(self) -> TumblerState:
        return self._state

    def load_state(self, state: TumblerState) -> None:
        self._state = state
        self._recalculate_current_height()
