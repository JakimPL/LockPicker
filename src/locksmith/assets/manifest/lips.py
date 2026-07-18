from locksmith.assets.manifest.sprite import SpriteAsset
from locksmith.schema.models.base import SceneModel


class LipAssets(SceneModel):
    """Shear-lip strips; each `tip_anchor` row lands on its shear line."""

    upper: SpriteAsset
    lower: SpriteAsset
