from locksmith.schema.models.anatomy.bevel import EdgeBevel
from locksmith.schema.models.anatomy.pin.collar import CollarAnatomy
from locksmith.schema.models.base import SceneModel


class PinAnatomy(SceneModel):
    """Full-height tumbler pin proportions, origin at the free tip.

    The shoulder bevel curves the front face so the gradient environment
    sweeps a reflection across it; a flat front reads as wood under the
    orthographic camera.
    """

    width_margin: float
    depth: float
    shoulder_bevel: EdgeBevel
    back_bevel: EdgeBevel
    tip_bevel: EdgeBevel
    collar: CollarAnatomy
