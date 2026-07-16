from locksmith.config.models.base import SceneModel


class EdgeWearConfig(SceneModel):
    """Pointiness ramp brightening convex edges; handled metal wears shiny."""

    start: float
    end: float
    strength: float
