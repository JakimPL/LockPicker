from locksmith.config.models.base import SceneModel
from locksmith.types import Vec3


class PoolConfig(SceneModel):
    """Painted lamp pool; localized light lives only in the background plate."""

    location: Vec3
    scale: float
    strength: float
    key_mix: float
    gain: float
