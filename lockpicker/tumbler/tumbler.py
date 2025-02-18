from dataclasses import replace
from typing import Optional

from lockpicker.tumbler.base import BaseTumbler
from lockpicker.tumbler.location import Location
from lockpicker.tumbler.state import TumblerState


class Tumbler:
    def __init__(
        self,
        base: BaseTumbler,
        state: Optional[TumblerState] = None,
        counter: Optional["Tumbler"] = None,
    ):
        self._base = base
        self._state = TumblerState(base.height) if state is None else state
        self._counter = counter

    def __repr__(self) -> str:
        return (
            f"Tumbler(location={self.location}, group={self.group}, height={self.base_height}, "
            f"max_height={self.max_height}, post_release_height={self.post_release_height}, master={self.master}, "
            f"current_height={self._state.current_height}, pushed={self._state.pushed}, "
            f"jammed={self._state.jammed}, release={self._state.release}, difference={self._state.difference})"
        )

    def copy(self) -> "Tumbler":
        return Tumbler(
            self.base,
            self.state.copy(),
            self.counter,
        )

    def jam(self):
        self._state.release = False
        self._state.jammed = True
        self._state.pushed = True

    def push(self):
        self._state.release = False
        self._state.pushed = True
        self._recalculate_current_height()

    def unjam(self):
        self._state.release = False
        self._state.jammed = False

    def release(self, direct: bool = False):
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

    def _recalculate_current_height(self):
        if self.pushed:
            height = 1
        else:
            height = self.base_height + self.difference
            if self.release:
                height += self.post_release_height

        self._state.counter_height = self._counter.height if self._counter is not None else 0
        self._state.current_height = max(1, min(height, self.max_height - self._state.counter_height))

    @property
    def base_height(self) -> int:
        return self._base.height

    @height.setter
    def height(self, height: int):
        if not isinstance(height, int):
            raise TypeError(f"Height must be an integer, got {type(height)}")
        if height < 1:
            raise ValueError(f"Height must be at least 1, got {height}")
        if height > self.max_height:
            raise ValueError(f"Height must be at most {self.max_height}, got {height}")

        self._base = replace(self._base, height=height)
        self._recalculate_current_height()

    @property
    def location(self) -> Location:
        return self._base.location

    @property
    def position(self) -> int:
        return self._base.location.position

    @property
    def upper(self) -> bool:
        return self._base.location.upper

    @property
    def group(self) -> int:
        return self._base.group

    @group.setter
    def group(self, group: int):
        if not isinstance(group, int):
            raise TypeError(f"Group must be an integer, got {type(group)}")
        if group < 0:
            raise ValueError(f"Group must be non-negative, got {group}")

        self._base = replace(self._base, group=group)

    @property
    def master(self) -> bool:
        return self._base.master

    @master.setter
    def master(self, master: bool):
        if not isinstance(master, bool):
            raise TypeError(f"Master must be a boolean, got {type(master)}")

        self._base = replace(self._base, master=master)

    @property
    def post_release_height(self) -> int:
        return self._base.post_release_height

    @post_release_height.setter
    def post_release_height(self, height: int):
        if not isinstance(height, int):
            raise TypeError(f"Post-release height must be an integer, got {type(height)}")

        self._base = replace(self._base, post_release_height=height)

    @property
    def difference(self) -> int:
        return self._state.difference

    def set_difference(self, difference: int, recalculate: bool = True):
        if not isinstance(difference, int):
            raise TypeError(f"Difference must be an integer, got {type(difference)}")

        self._state.difference = difference
        if recalculate:
            self._recalculate_current_height()

    @property
    def max_height(self) -> int:
        return self._base.max_height

    @property
    def counter(self) -> Optional["Tumbler"]:
        return self._counter

    @counter.setter
    def counter(self, counter: Optional["Tumbler"]):
        if not isinstance(counter, Tumbler) and counter is not None:
            raise ValueError(f"Counter must be a Tumbler instance, got {type(counter)}")

        self._counter = counter
        self._recalculate_current_height()

    @property
    def free(self) -> bool:
        return self.height <= 1

    @property
    def base(self) -> BaseTumbler:
        return self._base

    @property
    def state(self) -> TumblerState:
        return self._state

    def serialize(self) -> bytes:
        return self._base.serialize()

    @classmethod
    def deserialize(cls, data: bytes, max_height: int) -> "Tumbler":
        base = BaseTumbler.deserialize(data, max_height)
        return Tumbler(base)
