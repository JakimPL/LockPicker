from locksmith.schema.models.base import SceneModel


class HoverConfig(SceneModel):
    """Facing-weighted emission rim; the pin reads as lit, never recolored."""

    blend: float
    power: float
    gain: float
