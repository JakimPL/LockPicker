from locksmith.schema.models.base import SceneModel
from locksmith.types import HexColor


class MetalColors(SceneModel):
    base: HexColor
    highlight: HexColor
