from locksmith.schema.models.base import SceneModel


class ShadowCatcherAnatomy(SceneModel):
    """Shadow-only trough replica the pin shadow sprites bake onto.

    The catcher copies one column's bore trough so the baked shadow bends
    with the curved surface it lands on at runtime; `margin` stretches it
    vertically past the visible board like the real troughs.
    """

    margin: float
