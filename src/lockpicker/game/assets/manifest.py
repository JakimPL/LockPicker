from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Final, Tuple

from pydantic import BaseModel, ConfigDict

from lockpicker.constants.config import PickShape

MANIFEST_FILENAME: Final[str] = "manifest.json"

PixelPair = Tuple[int, int]


class ManifestModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class RenderProvenance(ManifestModel):
    blender_version: str
    engine: str
    samples: int
    seed: int
    view_transform: str
    look: str
    exposure: float


class SpriteAsset(ManifestModel):
    image: str
    size: PixelPair
    tip_anchor: PixelPair


class BadgeAsset(ManifestModel):
    image: str
    size: PixelPair
    center_anchor: PixelPair
    tip_offset_pixels: float


class BadgesAssets(ManifestModel):
    master: BadgeAsset


class TumblerOrientationAssets(ManifestModel):
    images: Dict[str, str]
    size: PixelPair
    tip_anchor: PixelPair
    shadow: SpriteAsset


class TumblerAssets(ManifestModel):
    full_height_units: float
    pixels_per_height_unit: float
    column_width_pixels: float
    groups: Tuple[str, ...]
    upper: TumblerOrientationAssets
    lower: TumblerOrientationAssets


class BoardAssets(ManifestModel):
    logical_size: PixelPair
    background: str
    frame: str


class ThemeManifest(ManifestModel):
    schema_version: int
    theme: str
    image_scale: int
    provenance: RenderProvenance
    board: BoardAssets
    tumblers: TumblerAssets
    picks: Dict[PickShape, SpriteAsset]
    badges: BadgesAssets


def load_manifest(directory: Path) -> ThemeManifest:
    return ThemeManifest.model_validate(json.loads((directory / MANIFEST_FILENAME).read_text()))
