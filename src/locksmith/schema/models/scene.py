from locksmith.schema.models.anatomy.anatomy import AnatomyConfig
from locksmith.schema.models.assets import AssetsConfig
from locksmith.schema.models.base import SceneModel
from locksmith.schema.models.board import BoardConfig
from locksmith.schema.models.lighting.lighting import LightingConfig
from locksmith.schema.models.lookdev.lookdev import LookdevConfig
from locksmith.schema.models.palette.palette import PaletteConfig
from locksmith.schema.models.rendering import RenderConfig
from locksmith.schema.models.shading.shading import ShadingConfig
from locksmith.schema.models.staging import StagingConfig
from locksmith.schema.models.views.views import ViewsConfig
from locksmith.schema.models.world import WorldConfig


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
