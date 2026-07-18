from locksmith.schema.models.base import SceneModel


class GripConfig(SceneModel):
    """Waxed cord wrap: banded wave bump, with the palette color dimmed toward the scene's values."""

    roughness: float
    wave_scale: float
    bump_strength: float
    dim_factor: float
