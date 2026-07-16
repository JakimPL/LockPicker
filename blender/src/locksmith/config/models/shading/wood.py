from locksmith.config.models.base import SceneModel


class WoodConfig(SceneModel):
    """Procedural plank wood: distorted wave grain stretched along the plank axis.

    `stretch` squashes the z axis of the grain coordinates, turning the wave
    bands into long vertical streaks; `tone_*` drives a large-scale noise that
    varies the overall stain from area to area.
    """

    specular: float
    roughness: float
    ring_scale: float
    ring_detail: float
    distortion: float
    stretch: float
    tone_scale: float
    tone_detail: float
    tone_strength: float
    bump_strength: float
