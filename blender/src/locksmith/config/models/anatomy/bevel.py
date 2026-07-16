from locksmith.config.models.base import SceneModel


class EdgeBevel(SceneModel):
    offset: float
    segments: int
    profile: float
