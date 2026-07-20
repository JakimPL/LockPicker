from typing import Tuple

from locksmith.schema.models.anatomy.screws.head import ScrewHead
from locksmith.schema.models.anatomy.screws.slot import ScrewSlot
from locksmith.schema.models.base import SceneModel


class FlangeAnatomy(SceneModel):
    """Vertical angle-iron seam strips fastening the case onto the bench wood.

    One strip sits proud on each wood/case joint; fastener heads march along
    it at `spacing_z`, with `slot_angles` cycling per fastener to sell hand
    assembly.
    """

    width_pixels: float
    face_y: float
    depth: float
    margin: float
    spacing_z: float
    slot_angles: Tuple[float, ...]
    head: ScrewHead
    slot: ScrewSlot
