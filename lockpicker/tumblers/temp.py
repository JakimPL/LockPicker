from dataclasses import dataclass


@dataclass(frozen=True)
class TempTumbler:
    pushed: bool
    jammed: bool
    release: bool
    difference: int
    current_height: int
