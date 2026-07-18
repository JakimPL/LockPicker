from locksmith.schema.models.base import SceneModel
from locksmith.types import PixelPair


class BoardAssets(SceneModel):
    """Full-board plates: the opaque back layer and the transparent overlay."""

    logical_size: PixelPair
    background: str
    frame: str
