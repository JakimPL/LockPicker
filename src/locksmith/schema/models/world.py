from locksmith.schema.models.base import SceneModel


class WorldConfig(SceneModel):
    """Gradient environment the curved metal surfaces sweep across.

    The gradient value is `z_factor * z + x_factor * x` over the sky sphere,
    ramping from the floor color through the mid tone to a warm bright
    top-left, so machined shoulders pick up a sweeping reflection under the
    orthographic camera.
    """

    z_factor: float
    x_factor: float
    mid_position: float
    top_white_mix: float
    top_gain: float
    strength: float
