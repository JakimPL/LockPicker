from locksmith.config.models.anatomy.pick.circle_tip import CircleTipAnatomy
from locksmith.config.models.anatomy.pick.diamond_tip import DiamondTipAnatomy
from locksmith.config.models.anatomy.pick.ferrule import FerruleAnatomy
from locksmith.config.models.anatomy.pick.grip import GripAnatomy
from locksmith.config.models.anatomy.pick.shaft import ShaftAnatomy
from locksmith.config.models.base import SceneModel


class PickAnatomy(SceneModel):
    """Pick tool along the x axis, origin at the tip; parts extend leftward off screen."""

    shaft: ShaftAnatomy
    diamond_tip: DiamondTipAnatomy
    circle_tip: CircleTipAnatomy
    ferrule: FerruleAnatomy
    grip: GripAnatomy
