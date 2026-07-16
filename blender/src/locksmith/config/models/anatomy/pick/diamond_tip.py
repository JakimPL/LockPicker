from locksmith.config.models.base import SceneModel


class DiamondTipAnatomy(SceneModel):
    """Cube spun 45° around the shaft axis; sized so the half-diagonal matches the game's pick size."""

    width: float
    depth: float
    height: float
