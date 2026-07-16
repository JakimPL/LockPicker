from typing import Dict

from locksmith.assets.manifest.sprite import SpriteAsset
from locksmith.config.models.base import SceneModel
from locksmith.types import Metal, PixelPair


class TumblerOrientationAssets(SceneModel):
    """Sprites of one pin orientation; all metal variants share one framing.

    Upper and lower pins are rendered separately because mirroring a sprite
    would flip its baked key light.
    """

    images: Dict[Metal, str]
    size: PixelPair
    tip_anchor: PixelPair
    shadow: SpriteAsset
