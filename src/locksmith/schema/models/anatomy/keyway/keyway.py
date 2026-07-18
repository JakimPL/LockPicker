from locksmith.schema.models.anatomy.keyway.bushing import KeywayBushing
from locksmith.schema.models.base import SceneModel


class KeywayAnatomy(SceneModel):
    """Tool slot through the bench panel, between the shear lines.

    The mouth is a narrow vertical opening in the wood the picks reach
    through, framed by proud brass wear liners and floored by the dark
    raceway bed behind it. `overshoot` extends the bed and liners past the
    slot opening and past the shear lines so their ends tuck behind the
    wood and the lip rails.
    """

    center_pixels: float
    width_pixels: float
    bed_face_y: float
    back_y: float
    overshoot: float
    bushing: KeywayBushing
