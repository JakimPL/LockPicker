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

    def copy(self) -> "Tumbler":
        return Tumbler(
            self.position,
            self.upper,
            self.group,
            self.base_height,
            self.post_release_height,
            self.master,
        )

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
        if self.pushed:
            return 1

        height = self._height + self.difference
        if self._release:
            height += self.post_release_height

        return max(1, height)

    @property
    def base_height(self) -> int:
        return self._height

    @height.setter
    def height(self, height: int):
        self._height = height

    @property
    def position(self) -> int:
        return self._position

    @property
    def upper(self) -> bool:
        return self._upper

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
        self._post_release_height = round(height)

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
