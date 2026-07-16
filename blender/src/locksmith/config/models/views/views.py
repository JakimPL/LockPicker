from locksmith.config.models.base import SceneModel


class ViewsConfig(SceneModel):
    """Shared camera placement; every framing looks down +y from this depth.

    The board camera derives its width from the board itself and the batch
    pipeline computes each sprite framing from prototype geometry, so only
    the viewing axis lives in config.
    """

    camera_y: float
    clip_start: float
    clip_end: float
