from locksmith.config.models.base import SceneModel


class BackgroundAnatomy(SceneModel):
    """Deep back wall plus one bore trough per column in front of it.

    `pocket_y` places each trough's rim plane; the concave surface reaches
    `pocket_y` plus its radius toward the wall, so the rims must sit far
    enough forward that the deepest line stays in front of the wall face.
    `pocket_segments` counts the full circle the trough is cut from and must
    be a multiple of four.
    """

    margin: float
    depth: float
    center_y: float
    pocket_y: float
    pocket_segments: int
