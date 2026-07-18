from locksmith.schema.models.base import SceneModel
from locksmith.schema.models.lighting.sun import SunConfig


class LightingConfig(SceneModel):
    key: SunConfig
    rim: SunConfig
