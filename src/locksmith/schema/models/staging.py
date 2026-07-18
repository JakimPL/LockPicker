from locksmith.schema.models.base import SceneModel


class StagingConfig(SceneModel):
    """Parking positions for the prototype objects outside the board view.

    The batch pipeline frames each parked prototype from its mesh bounds, so
    the positions only need to keep the prototypes off the board and apart
    from each other.
    """

    tumbler_upper_x: float
    tumbler_lower_x: float
    pick_x: float
    pick_diamond_z: float
    pick_circle_z: float
    badge_x: float
    badge_z: float
