from pathlib import Path
from typing import Dict, Final

from locksmith.assets.manifest.badges import BadgesAssets
from locksmith.assets.manifest.board import BoardAssets
from locksmith.assets.manifest.lips import LipAssets
from locksmith.assets.manifest.provenance import RenderProvenance
from locksmith.assets.manifest.sprite import SpriteAsset
from locksmith.assets.manifest.tumblers import TumblerAssets
from locksmith.schema.models.base import SceneModel
from locksmith.types import PickShape

MANIFEST_FILENAME: Final[str] = "manifest.json"
JSON_INDENT: Final[int] = 4


class ThemeManifest(SceneModel):
    """Framework-agnostic description of one rendered theme.

    All coordinates are logical board pixels; `image_scale` marks how many
    image pixels each logical pixel spans, so a runtime can supersample or
    scale down without re-rendering.
    """

    schema_version: int
    theme: str
    image_scale: int
    provenance: RenderProvenance
    board: BoardAssets
    tumblers: TumblerAssets
    picks: Dict[PickShape, SpriteAsset]
    badges: BadgesAssets
    lips: LipAssets


def write_manifest(manifest: ThemeManifest, path: Path) -> None:
    path.write_text(manifest.model_dump_json(indent=JSON_INDENT) + "\n", encoding="utf-8")


def load_manifest(path: Path) -> ThemeManifest:
    return ThemeManifest.model_validate_json(path.read_text(encoding="utf-8"))
