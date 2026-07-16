from locksmith.config.models.base import SceneModel
from locksmith.config.models.shading.bevel_normal import BevelNormalConfig
from locksmith.config.models.shading.breakup import BreakupConfig
from locksmith.config.models.shading.edge_wear import EdgeWearConfig
from locksmith.config.models.shading.hover import HoverConfig
from locksmith.config.models.shading.jam import JamConfig
from locksmith.config.models.shading.patina import PatinaConfig
from locksmith.config.models.shading.roughness import MetalRoughness


class MetalsConfig(SceneModel):
    roughness: MetalRoughness
    breakup: BreakupConfig
    edge_wear: EdgeWearConfig
    bevel_normal: BevelNormalConfig
    patina: PatinaConfig
    hover: HoverConfig
    jam: JamConfig
