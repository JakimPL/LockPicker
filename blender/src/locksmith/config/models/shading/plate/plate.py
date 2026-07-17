from locksmith.config.models.base import SceneModel
from locksmith.config.models.shading.plate.depth_fade import DepthFadeConfig
from locksmith.config.models.shading.plate.mottle import MottleConfig
from locksmith.config.models.shading.plate.pool import PoolConfig
from locksmith.config.models.shading.plate.rim import RimConfig
from locksmith.config.models.shading.plate.shell import ShellBand


class PlateShading(SceneModel):
    """Self-lit painted plate at exact palette values.

    Emission keeps the plate's values fixed under any light rig — a
    physically shaded plate kept outshining the pins and inverting the value
    hierarchy — while the surface still blocks light, so the rails cast
    correct shadows on the pins.
    """

    emission_strength: float
    mottle: MottleConfig
    rim: RimConfig
    pool: PoolConfig
    shell: ShellBand
    depth_fade: DepthFadeConfig
