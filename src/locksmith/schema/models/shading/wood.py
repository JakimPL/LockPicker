from locksmith.schema.models.base import SceneModel


class WoodConfig(SceneModel):
    """Procedural plank wood: broad figure under distorted latewood grain.

    `figure_*` drives a slow anisotropic noise streaked along the plank
    (`figure_stretch` squashes its z axis) that lifts earlywood zones toward
    the lighter tone, giving board-to-board figure. `stretch` likewise squashes
    the faster grain wave into long vertical latewood lines, mixed toward the
    dark stain by `grain_contrast` and warbled by `detail_roughness` so they
    read irregular; `roughness_variation` makes those lines a touch glossier.
    `tone_*` adds a large-scale stain drift over the whole panel. `pore_*` is a
    fine grain-aligned noise added to the bump — pore and sanding micro-relief
    between the latewood lines — so the sun breaks up across the surface and the
    planks read as worked timber instead of a smooth crowned gradient, even on
    the shadowed side of the board where albedo grain washes out.
    """

    specular: float
    roughness: float
    ring_scale: float
    ring_detail: float
    distortion: float
    detail_roughness: float
    grain_contrast: float
    stretch: float
    figure_scale: float
    figure_detail: float
    figure_stretch: float
    figure_strength: float
    tone_scale: float
    tone_detail: float
    tone_strength: float
    roughness_variation: float
    pore_scale: float
    pore_detail: float
    pore_strength: float
    bump_strength: float
