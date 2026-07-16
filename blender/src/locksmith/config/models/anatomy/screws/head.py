from locksmith.config.models.base import SceneModel


class ScrewHead(SceneModel):
    """Countersunk head; the base sits against the plate and the face tapers toward the camera."""

    segments: int
    base_radius: float
    face_radius: float
    depth: float
    y: float
