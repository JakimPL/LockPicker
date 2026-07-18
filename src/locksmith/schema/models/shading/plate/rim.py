from locksmith.schema.models.base import SceneModel


class RimConfig(SceneModel):
    start: float
    end: float
    strength: float
    key_mix: float
    gain: float
