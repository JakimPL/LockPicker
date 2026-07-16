from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import pygame

from lockpicker.constants.config import PickShape, settings
from lockpicker.game.assets.library import AssetLibrary
from lockpicker.game.assets.manifest import PixelPair
from lockpicker.game.layout import Layout


@dataclass(frozen=True)
class ScaledSprite:
    surface: pygame.surface.Surface
    anchor: PixelPair


def scaled_pair(pair: PixelPair, *, scale_x: float, scale_y: float) -> PixelPair:
    return round(pair[0] * scale_x), round(pair[1] * scale_y)


class ThemeSprites:
    def __init__(self, library: AssetLibrary, layout: Layout) -> None:
        manifest = library.manifest
        self.scale_x = settings.layout.bar_width / manifest.tumblers.column_width_pixels
        self.scale_y = layout.scale / manifest.tumblers.pixels_per_height_unit

        screen_size = (settings.screen.width, settings.screen.height)
        self.background = pygame.transform.smoothscale(library.surface(manifest.board.background), screen_size)
        self.frame = pygame.transform.smoothscale(library.surface(manifest.board.frame), screen_size)

        self._tumblers: Dict[Tuple[int, bool, bool], ScaledSprite] = {}
        for upper, orientation in ((True, manifest.tumblers.upper), (False, manifest.tumblers.lower)):
            size = self._scaled(orientation.size)
            anchor = self._scaled(orientation.tip_anchor)
            for group, metal in enumerate(manifest.tumblers.groups):
                base = pygame.transform.smoothscale(library.surface(orientation.images[metal]), size)
                hover = base.copy()
                hover.fill(settings.theme.highlight_tint, special_flags=pygame.BLEND_RGB_ADD)
                self._tumblers[(group, upper, False)] = ScaledSprite(base, anchor)
                self._tumblers[(group, upper, True)] = ScaledSprite(hover, anchor)

        self._picks: Dict[PickShape, ScaledSprite] = {}
        for shape, asset in manifest.picks.items():
            surface = pygame.transform.smoothscale(library.surface(asset.image), self._scaled(asset.size))
            self._picks[shape] = ScaledSprite(surface, self._scaled(asset.tip_anchor))

    def _scaled(self, pair: PixelPair) -> PixelPair:
        return scaled_pair(pair, scale_x=self.scale_x, scale_y=self.scale_y)

    def tumbler(self, group: int, *, upper: bool, highlighted: bool) -> ScaledSprite:
        return self._tumblers[(group, upper, highlighted)]

    def pick(self, shape: PickShape) -> ScaledSprite:
        return self._picks[shape]
