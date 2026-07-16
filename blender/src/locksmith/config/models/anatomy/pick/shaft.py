from locksmith.config.models.base import SceneModel


class ShaftAnatomy(SceneModel):
    segments: int
    radius: float
    length: float
    center_x: float
