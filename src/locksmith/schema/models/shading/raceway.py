from locksmith.schema.models.base import SceneModel
from locksmith.types import Vec3


class RacewayShading(SceneModel):
    """Lit worn floor for the keyway mouth: brushed along the picks.

    Horizontal wear streaks distinguish the entry from the chamber behind
    the pins; because the material is lit, the carved band edges above and
    below cast real shadows onto the bed, so the mouth reads as recessed
    rather than painted. `glow` is the emission floor that keeps the streak
    pattern alive inside those shadows. `patina_mix` cools the bed toward
    verdigris — the one crevice on the panel old enough to have grown it —
    so the warm board carries a single contrasting note behind the picks.
    """

    base_mix: float
    patina_mix: float
    streak_mapping_scale: Vec3
    noise_scale: float
    noise_detail: float
    strength: float
    key_mix: float
    gain: float
    metallic: float
    roughness: float
    specular: float
    glow: float
