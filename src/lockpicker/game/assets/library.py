from __future__ import annotations

from pathlib import Path
from typing import Dict

import pygame

from lockpicker.constants.config import settings
from lockpicker.game.assets.manifest import ThemeManifest, load_manifest
from lockpicker.paths import PROJECT_ROOT


def theme_directory() -> Path:
    return PROJECT_ROOT / settings.theme.directory / settings.theme.name


def validate_manifest(manifest: ThemeManifest) -> None:
    if len(manifest.tumblers.groups) != len(settings.color.tumblers):
        raise ValueError(
            f"manifest defines {len(manifest.tumblers.groups)} tumbler groups, "
            f"config defines {len(settings.color.tumblers)}"
        )

    screen_size = (settings.screen.width, settings.screen.height)
    if manifest.board.logical_size != screen_size:
        raise ValueError(f"manifest board size {manifest.board.logical_size} does not match screen {screen_size}")

    missing_shapes = set(settings.pick.shapes) - set(manifest.picks)
    if missing_shapes:
        raise ValueError(f"manifest is missing pick shapes: {sorted(shape.value for shape in missing_shapes)}")


class AssetLibrary:
    def __init__(self, manifest: ThemeManifest, directory: Path) -> None:
        self.manifest = manifest
        self.directory = directory
        self._surfaces: Dict[str, pygame.surface.Surface] = {}

    @classmethod
    def load(cls) -> AssetLibrary:
        directory = theme_directory()
        manifest = load_manifest(directory)
        validate_manifest(manifest)
        return cls(manifest, directory)

    def surface(self, image: str) -> pygame.surface.Surface:
        if image not in self._surfaces:
            self._surfaces[image] = pygame.image.load(self.directory / image).convert_alpha()

        return self._surfaces[image]
