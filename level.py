from dataclasses import dataclass
from typing import Dict, List, Tuple

from tumbler import Tumbler


@dataclass
class Level:
    tumblers: List[Tumbler]
    rules: Dict[Tuple[int, bool], List[Tuple[int, bool, int]]]
