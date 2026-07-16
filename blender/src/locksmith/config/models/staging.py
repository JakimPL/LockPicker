from locksmith.config.models.base import SceneModel


class StagingConfig(SceneModel):
    """Parking positions for the prototype objects outside the board view.

    Each prototype must stay centered in its sprite camera's frame, so these
    x positions pair with the matching entries in `ViewsConfig.sprites`.
    """

    tumbler_upper_x: float
    tumbler_lower_x: float
    pick_x: float
    pick_diamond_z: float
    pick_circle_z: float
    badge_x: float
    badge_z: float
