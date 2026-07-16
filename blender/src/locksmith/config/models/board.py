from locksmith.config.models.base import SceneModel


class BoardConfig(SceneModel):
    """Logical screen layout of the game board, in pixels.

    The calibration contract is 1 Blender world unit = 1 tumbler height unit
    = `pixels_per_unit` logical pixels; `max_height` is the full travel of a
    tumbler and therefore the authored pin length.
    """

    pixels_per_unit: float
    width_pixels: float
    height_pixels: float
    column_width_pixels: float
    column_pitch_pixels: float
    column_offset_pixels: float
    columns: int
    max_height: float
