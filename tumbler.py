class Tumbler:
    def __init__(
            self,
            position: int,
            upper: bool,
            group: int,
            height: int,
            master: bool = False,
            jammed: bool = False
    ):
        self.position = position
        self.upper = upper
        self.height = height
        self.group = group
        self.master = master
        self.jammed = jammed

        self.difference = 0
        self.pushed = False

    @property
    def current_height(self):
        return self.height + self.difference if not self.pushed else 1
