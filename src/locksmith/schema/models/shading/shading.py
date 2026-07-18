from locksmith.schema.models.base import SceneModel
from locksmith.schema.models.shading.bore import BoreConfig
from locksmith.schema.models.shading.enamel import EnamelConfig
from locksmith.schema.models.shading.grip import GripConfig
from locksmith.schema.models.shading.metals import MetalsConfig
from locksmith.schema.models.shading.plate.plate import PlateShading
from locksmith.schema.models.shading.pocket import PocketShading
from locksmith.schema.models.shading.raceway import RacewayShading
from locksmith.schema.models.shading.wood import WoodConfig


class ShadingConfig(SceneModel):
    metals: MetalsConfig
    plate: PlateShading
    bore: BoreConfig
    enamel: EnamelConfig
    grip: GripConfig
    wood: WoodConfig
    pocket: PocketShading
    raceway: RacewayShading
