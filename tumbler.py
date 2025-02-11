class Tumbler:
    def __init__(
            self,
            position: int,
            upper: bool,
            group: int,
            height: int,
            post_release_height: int = 0,
            master: bool = False
    ):
        self.position = position
        self.upper = upper
        self.group = group
        self.master = master
        self.post_release_height = post_release_height

        self.difference = 0
        self._pushed = False
        self._jammed = False
        self._height = height
        self._release = False

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
    def pushed(self):
        return self._pushed

    @property
    def jammed(self):
        return self._jammed

    @property
    def height(self):
        height = self._height + self.difference
        if self._release:
            height += self.post_release_height
        return height if not self.pushed else 1

    @property
    def base_height(self):
        return self._height
