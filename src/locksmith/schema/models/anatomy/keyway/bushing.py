from locksmith.schema.models.base import SceneModel


class KeywayBushing(SceneModel):
    """Brass wear liners framing the slot opening, proud of the bench face.

    `overshoot` extends the liners just past the shear lines — far enough
    that no gap shows under the lip rails, short enough that no brass pokes
    into the shell bands beyond them.
    """

    width_pixels: float
    face_y: float
    depth: float
    overshoot: float
