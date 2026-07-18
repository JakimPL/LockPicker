from enum import StrEnum
from typing import Annotated, Tuple

import numpy as np
from numpy.typing import NDArray
from pydantic import StringConstraints

RGBColor = Tuple[float, float, float]
RGBAColor = Tuple[float, float, float, float]
Vec3 = Tuple[float, float, float]
PixelPair = Tuple[int, int]
RGBAImage = NDArray[np.uint8]

HexColor = Annotated[str, StringConstraints(pattern=r"^[0-9A-F]{6}$")]


class Metal(StrEnum):
    STEEL = "steel"
    BRASS = "brass"
    COPPER = "copper"


class TumblerState(StrEnum):
    PLAIN = "plain"
    MASTER = "master"
    HOVER = "hover"
    JAM = "jam"


class PickShape(StrEnum):
    DIAMOND = "diamond"
    CIRCLE = "circle"
