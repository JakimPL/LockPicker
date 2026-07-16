from typing import Tuple

from locksmith.assets.manifest.tumbler_orientation import TumblerOrientationAssets
from locksmith.config.models.base import SceneModel
from locksmith.types import Metal


class TumblerAssets(SceneModel):
    """Tumbler sprites plus the calibration the runtime scales them by.

    `groups` maps the game's tumbler group indices onto metals, in order.
    """

    full_height_units: float
    pixels_per_height_unit: float
    column_width_pixels: float
    groups: Tuple[Metal, ...]
    upper: TumblerOrientationAssets
    lower: TumblerOrientationAssets
