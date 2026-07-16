from typing import Tuple

from locksmith.config.models.base import SceneModel


class RenderConfig(SceneModel):
    samples: int
    seed: int
    use_denoising: bool
    resolution: Tuple[int, int]
    film_transparent: bool
    view_transform: str
    look_candidates: Tuple[str, ...]
    exposure: float
