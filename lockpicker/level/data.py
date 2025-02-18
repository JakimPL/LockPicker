from typing import NamedTuple


class LevelData(NamedTuple):
    number_of_picks: bytes
    max_height: bytes
    serialized_tumblers: bytes
    serialized_bindings: bytes
