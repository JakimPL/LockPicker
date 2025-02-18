import struct
from typing import Optional

from lockpicker.location import Location


class Tumbler:
    struct_format = "i?iii?"

    def __init__(
        self,
        location: Location,
        group: int,
        height: int,
        max_height: int,
        post_release_height: int = 0,
        master: bool = False,
        counter: Optional["Tumbler"] = None,
    ):
        self._location = location
        self._group = group
        self._master = master
        self._height = height
        self._max_height = max_height
        self._post_release_height = post_release_height
        self._counter = counter

        self._pushed = False
        self._jammed = False
        self._release = False
        self._difference = 0
        self._current_height = height

    def __repr__(self) -> str:
        return f"Tumbler({self.location.position}, {self.location.upper}, {self.group}, {self.height}, master={self.master})"

    def copy(self) -> "Tumbler":
        return Tumbler(
            self.location,
            self.group,
            self.base_height,
            self.max_height,
            self.post_release_height,
            self.master,
            self.counter,
        )

    def jam(self):
        self._release = False
        self._jammed = True
        self._pushed = True

    def push(self):
        self._release = False
        self._pushed = True
        self._recalculate_current_height()

    def unjam(self):
        self._release = False
        self._jammed = False

    def release(self, direct: bool = False):
        self._jammed = False
        self._pushed = False
        self._release = direct
        if direct:
            self._difference = 0

        self._recalculate_current_height()

    @property
    def pushed(self) -> bool:
        return self._pushed

    @property
    def jammed(self) -> bool:
        return self._jammed

    @property
    def height(self) -> int:
        return self._current_height

    def _recalculate_current_height(self):
        if self.pushed:
            height = 1
        else:
            height = self._height + self.difference
            if self._release:
                height += self.post_release_height

        self._counter_height = self._counter.height if self._counter is not None else 0
        self._current_height = max(1, min(height, self.max_height - self._counter_height))

    @property
    def base_height(self) -> int:
        return self._height

    @height.setter
    def height(self, height: int):
        self._height = height
        self._recalculate_current_height()

    @property
    def location(self) -> Location:
        return self._location

    @property
    def position(self) -> int:
        return self._location.position

    @property
    def upper(self) -> bool:
        return self._location.upper

    @property
    def group(self) -> int:
        return self._group

    @group.setter
    def group(self, group: int):
        if group < 0:
            raise ValueError(f"Group must be non-negative, got {group}")
        self._group = group

    @property
    def master(self) -> bool:
        return self._master

    @master.setter
    def master(self, master: bool):
        self._master = master

    @property
    def post_release_height(self) -> int:
        return self._post_release_height

    @post_release_height.setter
    def post_release_height(self, height: int):
        self._post_release_height = height

    @property
    def difference(self) -> int:
        return self._difference

    def set_difference(self, difference: int, recalculate: bool = True):
        self._difference = difference
        if recalculate:
            self._recalculate_current_height()

    @property
    def max_height(self) -> int:
        return self._max_height

    @property
    def counter(self) -> Optional["Tumbler"]:
        return self._counter

    @counter.setter
    def counter(self, counter: Optional["Tumbler"]):
        if not isinstance(counter, Tumbler) and counter is not None:
            raise ValueError(f"Counter must be a Tumbler instance")
        self._counter = counter
        self._recalculate_current_height()

    def serialize(self) -> bytes:
        return struct.pack(
            self.struct_format,
            self.position,
            self.upper,
            self.group,
            self.base_height,
            self.post_release_height,
            self.master,
        )

    @property
    def free(self) -> bool:
        return self.height <= 1

    @classmethod
    def deserialize(cls, data: bytes, max_height: int) -> "Tumbler":
        position, upper, group, height, post_release_height, master = struct.unpack(cls.struct_format, data)
        return Tumbler(Location(position, upper), group, height, max_height, post_release_height, master)
