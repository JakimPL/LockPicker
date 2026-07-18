from locksmith.schema.models.base import SceneModel


class ScrewPlacement(SceneModel):
    """One screw on the plate; varied slot angles sell hand assembly."""

    x: float
    z: float
    slot_angle: float
