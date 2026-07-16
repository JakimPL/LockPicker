from locksmith.config.models.base import SceneModel


class InlayAnatomy(SceneModel):
    segments: int
    radius: float
    depth: float
    y: float
