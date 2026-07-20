from locksmith.schema.models.base import SceneModel


class FerruleAnatomy(SceneModel):
    segments: int
    radius: float
    length: float
    center_x: float
