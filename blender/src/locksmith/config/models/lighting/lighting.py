from locksmith.config.models.base import SceneModel
from locksmith.config.models.lighting.sun import SunConfig


class LightingConfig(SceneModel):
    key: SunConfig
    rim: SunConfig
