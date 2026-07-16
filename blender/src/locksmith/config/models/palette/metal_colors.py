from locksmith.config.models.base import SceneModel
from locksmith.types import HexColor


class MetalColors(SceneModel):
    base: HexColor
    highlight: HexColor
