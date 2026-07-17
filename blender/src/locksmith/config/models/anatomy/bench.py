from typing import Tuple

from locksmith.config.models.base import SceneModel


class BenchAnatomy(SceneModel):
    """Wooden plank panels flanking the housing plate.

    Planks march outward from each plate edge so any truncated plank lands
    off-screen; `depth_jitter` cycles per plank to break the front faces out
    of one plane, and `overlap` tucks the innermost plank behind the plate so
    no hairline of back wall can show at the seam. Between the shear lines
    the left panel sinks to `carve_face_y` — the raceway channel carved
    through the bench — while its shell bands stay proud at `face_y`.
    """

    face_y: float
    carve_face_y: float
    depth: float
    margin: float
    overshoot: float
    overlap: float
    plank_width: float
    gap: float
    depth_jitter: Tuple[float, ...]
