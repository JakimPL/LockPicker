from locksmith.config.models.base import SceneModel


class RingAnatomy(SceneModel):
    segments: int
    base_radius: float
    face_radius: float
    depth: float
    y: float
