from locksmith.schema.models.base import SceneModel
from locksmith.schema.models.shading.breakup import BreakupConfig


class BoreConfig(SceneModel):
    """Near-black diffuse iron for channel voids; low specular keeps the key sun out.

    The plate shadows the wall from almost every light, so `glow` adds a
    small self-lit floor of the bore color — without it the channels render
    as a pure void no palette value can lift.
    """

    specular: float
    roughness: float
    glow: float
    breakup: BreakupConfig
