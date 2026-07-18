from locksmith.schema.models.base import SceneModel
from locksmith.types import Vec3


class PocketShading(SceneModel):
    """Lit machined steel for the bore troughs behind each column.

    The trough geometry carries the depth — the suns shade the curve — so
    this material only zones the finish: polished pin-worn steel on the
    first-height-unit bands (|Z| past `half - offset_units`), duller and
    darker across the chamber run. The `*_sheen_mix` accents brighten
    toward the cool rim tone — polished steel reads gray, not warm — while
    the warm key sun supplies whatever warmth the lit walls carry. Three
    layers break up the bare gradient: `streak_*` lays vertical honing
    marks (pins slide along z, so the wear runs with them) whose noise also
    drives a bump so the marks catch the suns; `mottle_*` darkens broad
    soft patches toward the deep tone — the
    oil staining of a working mechanism; `cavity_*` sinks the camera-facing
    bore floor toward the deep tone so the concave groove reads as carved
    in, not bulging out; `patina_*` creeps verdigris into
    the crevices — the factor rises as the bore turns away from the camera,
    gated by its own noise so it patches instead of banding; and `ridge_*`
    brightens the sideways-facing rims where neighbouring troughs meet —
    the near cusps — fading to the far floor, painting the depth gradient
    the right way round so the groove reads as carved in. `glow` keeps a
    faint emission floor so jamb-shadowed parts of the bore never collapse
    to pure black. fBm noise crowds the middle of its range, which would
    turn the layer strengths into mean shifts instead of visible variation;
    `noise_low`/`noise_high` stretch that crowded band to a full 0..1 swing
    before any strength applies.
    """

    offset_units: float
    feather: float
    band_sheen_mix: float
    band_gain: float
    chamber_mix: float
    chamber_gain: float
    noise_low: float
    noise_high: float
    streak_mapping_scale: Vec3
    streak_scale: float
    streak_detail: float
    streak_strength: float
    streak_sheen_mix: float
    streak_gain: float
    mottle_scale: float
    mottle_detail: float
    mottle_strength: float
    cavity_start: float
    cavity_end: float
    cavity_strength: float
    patina_start: float
    patina_end: float
    patina_strength: float
    patina_scale: float
    patina_detail: float
    patina_mix: float
    patina_gain: float
    ridge_start: float
    ridge_end: float
    ridge_strength: float
    ridge_sheen_mix: float
    ridge_gain: float
    bump_strength: float
    metallic: float
    roughness: float
    specular: float
    glow: float
