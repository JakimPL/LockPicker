from locksmith.config.models.base import SceneModel
from locksmith.types import PixelPair


class BadgeAsset(SceneModel):
    """Marker sprite centered `tip_offset_pixels` beyond its tumbler's tip."""

    image: str
    size: PixelPair
    center_anchor: PixelPair
    tip_offset_pixels: float
