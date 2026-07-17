from locksmith.config.models.base import SceneModel
from locksmith.types import Vec3


class PocketShading(SceneModel):
    """Lit machined steel for the bore troughs behind each column.

    The trough geometry carries the depth — the suns shade the curve — so
    this material only zones the finish: polished pin-worn steel on the
    first-height-unit bands (|Z| past `half - offset_units`), duller and
    darker across the chamber run. Three layers break up the bare gradient:
    `streak_*` lays vertical honing marks (pins slide along z, so the wear
    runs with them) whose noise also drives a bump so the marks catch the
    suns; `mottle_*` darkens broad soft patches toward the deep tone — the
    oil staining of a working mechanism; and `wear_*` brightens a strip
    where the surface normal faces the camera — the polished wear line down
    the bore center where the pin actually rubs. `glow` keeps a faint
    emission floor so jamb-shadowed parts of the bore never collapse to
    pure black.
    """

    offset_units: float
    feather: float
    band_key_mix: float
    band_gain: float
    chamber_mix: float
    chamber_gain: float
    streak_mapping_scale: Vec3
    streak_scale: float
    streak_detail: float
    streak_strength: float
    streak_key_mix: float
    streak_gain: float
    mottle_scale: float
    mottle_detail: float
    mottle_strength: float
    wear_start: float
    wear_strength: float
    wear_key_mix: float
    wear_gain: float
    bump_strength: float
    metallic: float
    roughness: float
    specular: float
    glow: float
