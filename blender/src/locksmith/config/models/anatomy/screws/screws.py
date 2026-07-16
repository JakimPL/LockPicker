from typing import Tuple

from locksmith.config.models.anatomy.screws.head import ScrewHead
from locksmith.config.models.anatomy.screws.placement import ScrewPlacement
from locksmith.config.models.anatomy.screws.slot import ScrewSlot
from locksmith.config.models.base import SceneModel


class ScrewsAnatomy(SceneModel):
    head: ScrewHead
    slot: ScrewSlot
    placements: Tuple[ScrewPlacement, ...]
