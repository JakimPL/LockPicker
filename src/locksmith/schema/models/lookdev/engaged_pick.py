from locksmith.schema.models.base import SceneModel


class EngagedPickConfig(SceneModel):
    """Diamond pick pressed into the hovered tumbler, biting past its tip."""

    y: float
    bite_pixels: float
