from locksmith.config.models.base import SceneModel


class BevelNormalConfig(SceneModel):
    """Shader-side edge rounding; catches glints on edges the mesh keeps sharp."""

    radius: float
    samples: int
