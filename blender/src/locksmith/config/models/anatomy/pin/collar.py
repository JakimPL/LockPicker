from locksmith.config.models.anatomy.bevel import EdgeBevel
from locksmith.config.models.base import SceneModel


class CollarAnatomy(SceneModel):
    """Raised wear band near the pin tip; `tip_distance` keeps it within one height unit."""

    width_margin: float
    depth_margin: float
    height: float
    tip_distance: float
    bevel: EdgeBevel
