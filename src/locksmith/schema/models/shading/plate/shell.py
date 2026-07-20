from locksmith.schema.models.base import SceneModel


class ShellBand(SceneModel):
    """Brighter machined band on the first height unit at both board edges.

    The band marks the lock shell — the region a seated pin retracts into —
    so it starts `offset_units` inside each edge and eases in over `feather`
    world units toward the edge.
    """

    offset_units: float
    feather: float
    strength: float
    key_mix: float
    gain: float
