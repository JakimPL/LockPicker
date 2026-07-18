from locksmith.schema.models.base import SceneModel


class JamConfig(SceneModel):
    roughness_shift: float
    roughness_cap: float
