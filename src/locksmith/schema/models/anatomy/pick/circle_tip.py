from locksmith.schema.models.base import SceneModel


class CircleTipAnatomy(SceneModel):
    """Flattened sphere; the radius is given in logical pixels to match the game's pick size."""

    segments: int
    rings: int
    radius_pixels: float
    depth_scale: float
