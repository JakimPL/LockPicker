class Tumbler:
    def __init__(
            self,
            position: int,
            upper: bool,
            group: int,
            height: int,
            master: bool = False
    ):
        self.position = position
        self.upper = upper
        self.group = group
        self.master = master

        self.difference = 0
        self._pushed = False
        self._jammed = False
        self._height = height

    def jam(self):
        self._jammed = True
        self._pushed = True

    def push(self):
        self._pushed = True

    def unjam(self):
        self._jammed = False

    def release(self):
        self._jammed = False
        self._pushed = False

    @property
    def pushed(self):
        return self._pushed

    @property
    def jammed(self):
        return self._jammed

    @property
    def height(self):
        return self._height + self.difference if not self.pushed else 1

    @property
    def base_height(self):
        return self._height
