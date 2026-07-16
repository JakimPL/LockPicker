from locksmith.config.models.base import SceneModel
from locksmith.config.models.shading.bore import BoreConfig
from locksmith.config.models.shading.enamel import EnamelConfig
from locksmith.config.models.shading.grip import GripConfig
from locksmith.config.models.shading.metals import MetalsConfig
from locksmith.config.models.shading.plate.plate import PlateShading


class ShadingConfig(SceneModel):
    metals: MetalsConfig
    plate: PlateShading
    bore: BoreConfig
    enamel: EnamelConfig
    grip: GripConfig
