from locksmith.schema.models.anatomy.bevel import EdgeBevel
from locksmith.schema.models.base import SceneModel


class CollarAnatomy(SceneModel):
    """Raised wear band near the pin tip; `tip_distance` keeps it within one height unit."""

    width_margin: float
    depth_margin: float
    height: float
    tip_distance: float
    bevel: EdgeBevel
