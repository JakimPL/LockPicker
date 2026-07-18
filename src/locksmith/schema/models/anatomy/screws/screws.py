from typing import Tuple

from locksmith.schema.models.anatomy.screws.head import ScrewHead
from locksmith.schema.models.anatomy.screws.placement import ScrewPlacement
from locksmith.schema.models.anatomy.screws.slot import ScrewSlot
from locksmith.schema.models.base import SceneModel


class ScrewsAnatomy(SceneModel):
    head: ScrewHead
    slot: ScrewSlot
    placements: Tuple[ScrewPlacement, ...]
