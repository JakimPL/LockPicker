from locksmith.schema.models.base import SceneModel


class DepthFadeConfig(SceneModel):
    """Darkens surfaces by object-space depth so slot interiors go near-black."""

    near_y: float
    far_y: float
