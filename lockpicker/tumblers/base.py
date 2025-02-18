import struct
from dataclasses import dataclass

from lockpicker.location import Location

STRUCT_FORMAT = "i?iii?"


@dataclass(frozen=True)
class BaseTumbler:
    location: Location
    group: int
    height: int
    max_height: int
    post_release_height: int = 0
    master: bool = False

    def serialize(self) -> bytes:
        return struct.pack(
            STRUCT_FORMAT,
            self.location.position,
            self.location.upper,
            self.group,
            self.height,
            self.post_release_height,
            self.master,
        )

    @classmethod
    def deserialize(cls, data: bytes, max_height: int) -> "BaseTumbler":
        position, upper, group, height, post_release_height, master = struct.unpack(STRUCT_FORMAT, data)
        return BaseTumbler(Location(position, upper), group, height, max_height, post_release_height, master)
