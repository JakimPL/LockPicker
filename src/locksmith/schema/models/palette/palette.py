from locksmith.schema.models.base import SceneModel
from locksmith.schema.models.palette.metal_colors import MetalColors
from locksmith.types import HexColor


class PaletteConfig(SceneModel):
    """Every color in the scene, as sRGB hex; see docs/art-direction.md for roles."""

    key: HexColor
    rim: HexColor
    hover: HexColor
    enamel: HexColor
    jam: HexColor
    patina: HexColor
    plate: HexColor
    plate_dark: HexColor
    plate_deep: HexColor
    wood: HexColor
    wood_dark: HexColor
    wood_deep: HexColor
    wood_black: HexColor
    bore: HexColor
    world_floor: HexColor
    world_mid: HexColor
    rosette: HexColor
    steel: MetalColors
    brass: MetalColors
    copper: MetalColors
    lip: MetalColors
    pick: MetalColors
    grip_a: HexColor
    grip_b: HexColor
