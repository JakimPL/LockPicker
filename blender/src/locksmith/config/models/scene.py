from locksmith.config.models.anatomy.anatomy import AnatomyConfig
from locksmith.config.models.assets import AssetsConfig
from locksmith.config.models.base import SceneModel
from locksmith.config.models.board import BoardConfig
from locksmith.config.models.lighting.lighting import LightingConfig
from locksmith.config.models.lookdev.lookdev import LookdevConfig
from locksmith.config.models.palette.palette import PaletteConfig
from locksmith.config.models.rendering import RenderConfig
from locksmith.config.models.shading.shading import ShadingConfig
from locksmith.config.models.staging import StagingConfig
from locksmith.config.models.views.views import ViewsConfig
from locksmith.config.models.world import WorldConfig


class SceneConfig(SceneModel):
    board: BoardConfig
    palette: PaletteConfig
    anatomy: AnatomyConfig
    shading: ShadingConfig
    lighting: LightingConfig
    world: WorldConfig
    views: ViewsConfig
    staging: StagingConfig
    lookdev: LookdevConfig
    render: RenderConfig
    assets: AssetsConfig
