from locksmith.config.models.base import SceneModel
from locksmith.config.models.shading.breakup import BreakupConfig


class BoreConfig(SceneModel):
    """Near-black diffuse iron for channel voids; low specular keeps the key sun out."""

    specular: float
    roughness: float
    breakup: BreakupConfig
