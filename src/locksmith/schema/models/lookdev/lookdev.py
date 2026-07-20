from typing import Tuple

from locksmith.schema.models.base import SceneModel
from locksmith.schema.models.lookdev.engaged_pick import EngagedPickConfig
from locksmith.schema.models.lookdev.idle_pick import IdlePickConfig
from locksmith.schema.models.lookdev.tumbler import TumblerPlacement


class LookdevConfig(SceneModel):
    """Mock level arrangement mirroring docs/art/board-mock.png for review stills.

    The engaged pick attaches to the tumbler whose state is `hover`, so the
    list must contain exactly one hovered entry.
    """

    tumblers: Tuple[TumblerPlacement, ...]
    engaged_pick: EngagedPickConfig
    idle_pick: IdlePickConfig
