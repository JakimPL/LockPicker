from typing import Dict

from locksmith.config.models.base import SceneModel
from locksmith.config.models.views.sprite_view import SpriteViewConfig


class ViewsConfig(SceneModel):
    """Camera framings; the board camera derives its width from the board itself.

    Sprite views frame the parked prototypes, so each entry pairs with the
    matching `StagingConfig` position.
    """

    camera_y: float
    clip_start: float
    clip_end: float
    sprites: Dict[str, SpriteViewConfig]
