import struct


class Tumbler:
    struct_format = "i?iii?"

    def __init__(
        self,
        position: int,
        upper: bool,
        group: int,
        height: int,
        post_release_height: int = 0,
        master: bool = False,
    ):
        self._position = position
        self._upper = upper
        self._group = group
        self._master = master
        self._height = height
        self._post_release_height = post_release_height

        self.difference = 0
        self._pushed = False
        self._jammed = False
        self._release = False

    def __repr__(self) -> str:
        return f"Tumbler({self.position}, {self.upper}, {self.group}, {self.height}, master={self.master})"

    def jam(self):
        self._release = False
        self._jammed = True
        self._pushed = True

    def push(self):
        self._release = False
        self._pushed = True

    def unjam(self):
        self._release = False
        self._jammed = False

    def release(self, direct: bool = False):
        self._jammed = False
        self._pushed = False
        self._release = direct
        if direct:
            self.difference = 0

    @property
    def pushed(self) -> bool:
        return self._pushed

    @property
    def jammed(self) -> bool:
        return self._jammed

    @property
    def height(self) -> int:
        height = self._height + self.difference
        if self._release:
            height += self.post_release_height
        return height if not self.pushed else 1

    @property
    def base_height(self) -> int:
        return self._height

    @property
    def position(self) -> int:
        return self._position

    @property
    def upper(self) -> bool:
        return self._upper

    @property
    def group(self) -> int:
        return self._group

    @property
    def master(self) -> bool:
        return self._master

    @property
    def post_release_height(self) -> int:
        return self._post_release_height

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

    @classmethod
    def deserialize(cls, data: bytes) -> "Tumbler":
        position, upper, group, height, post_release_height, master = struct.unpack(cls.struct_format, data)
        return Tumbler(position, upper, group, height, post_release_height, master)
