from locksmith.config.models.base import SceneModel
from locksmith.types import PixelPair


class SpriteAsset(SceneModel):
    """One rendered sprite; sizes and anchors are in logical pixels.

    `tip_anchor` is the image pixel that must land on the sprite's anchored
    world point — a tumbler tip or a pick tip.
    """

    image: str
    size: PixelPair
    tip_anchor: PixelPair
