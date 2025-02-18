from dataclasses import dataclass, replace


@dataclass
class TumblerState:
    current_height: int
    pushed: bool = False
    jammed: bool = False
    release: bool = False
    difference: int = 0

    def copy(self):
        return replace(self)
