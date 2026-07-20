from locksmith.schema.models.base import SceneModel


class RenderProvenance(SceneModel):
    """Render choices baked into the committed images."""

    blender_version: str
    engine: str
    samples: int
    seed: int
    view_transform: str
    look: str
    exposure: float
