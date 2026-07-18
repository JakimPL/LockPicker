from locksmith.schema.models.base import SceneModel
from locksmith.schema.models.shading.bevel_normal import BevelNormalConfig
from locksmith.schema.models.shading.breakup import BreakupConfig
from locksmith.schema.models.shading.edge_wear import EdgeWearConfig
from locksmith.schema.models.shading.hover import HoverConfig
from locksmith.schema.models.shading.jam import JamConfig
from locksmith.schema.models.shading.patina import PatinaConfig
from locksmith.schema.models.shading.roughness import MetalRoughness


class MetalsConfig(SceneModel):
    roughness: MetalRoughness
    breakup: BreakupConfig
    edge_wear: EdgeWearConfig
    bevel_normal: BevelNormalConfig
    patina: PatinaConfig
    hover: HoverConfig
    jam: JamConfig
