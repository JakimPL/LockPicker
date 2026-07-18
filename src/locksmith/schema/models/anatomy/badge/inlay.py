from locksmith.schema.models.base import SceneModel


class InlayAnatomy(SceneModel):
    segments: int
    radius: float
    depth: float
    y: float
