from typing import Tuple

from locksmith.config.models.base import SceneModel


class BreakupConfig(SceneModel):
    """Roughness variation: fine noise spread plus streaks stretched along the object's z.

    The streak mapping scale squeezes noise into long vertical smears, giving
    the brushed-and-oiled finish; perfectly uniform roughness reads as plastic.
    """

    noise_scale: float
    noise_detail: float
    spread: float
    minimum: float
    streak_mapping_scale: Tuple[float, float, float]
    streak_scale: float
    streak_detail: float
    strength: float
