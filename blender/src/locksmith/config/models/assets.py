from typing import Tuple

from locksmith.config.models.base import SceneModel
from locksmith.types import Metal


class AssetsConfig(SceneModel):
    """Batch sprite pipeline parameters.

    `groups` maps the game's tumbler group indices onto metals, in order;
    `badge_tip_offset_pixels` is the runtime distance from a tumbler tip to
    its master badge center, published through the manifest.
    `pin_bake_tip_z` is the world height of a pin's tip while its sprite
    renders: the plate's painted glow varies across the board and reflects on
    the pins, so a translating sprite bakes the mid-travel appearance.
    """

    theme: str
    image_scale: int
    padding_pixels: int
    shadow_margin_pixels: int
    badge_tip_offset_pixels: float
    pin_bake_tip_z: float
    groups: Tuple[Metal, ...]
