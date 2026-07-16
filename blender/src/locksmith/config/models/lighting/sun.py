from locksmith.config.models.base import SceneModel
from locksmith.types import Vec3


class SunConfig(SceneModel):
    """Parallel-ray light; sprites translate at runtime, so falloff-free suns are mandatory."""

    direction: Vec3
    energy: float
    angle: float
