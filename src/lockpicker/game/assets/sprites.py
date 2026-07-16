from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

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


TumblerKey = Tuple[int, bool, bool, bool]


class ThemeSprites:
    def __init__(self, library: AssetLibrary, layout: Layout) -> None:
        manifest = library.manifest
        self.scale_x = settings.layout.bar_width / manifest.tumblers.column_width_pixels
        self.scale_y = layout.scale / manifest.tumblers.pixels_per_height_unit

        screen_size = (settings.screen.width, settings.screen.height)
        self.background = pygame.transform.smoothscale(library.surface(manifest.board.background), screen_size)
        self.frame = pygame.transform.smoothscale(library.surface(manifest.board.frame), screen_size)

        self._tumblers: Dict[TumblerKey, ScaledSprite] = {}
        self._faded: Dict[Tuple[TumblerKey, int], ScaledSprite] = {}
        self._shadows: Dict[bool, ScaledSprite] = {}
        for upper, orientation in ((True, manifest.tumblers.upper), (False, manifest.tumblers.lower)):
            size = self._scaled(orientation.size)
            anchor = self._scaled(orientation.tip_anchor)
            for group, metal in enumerate(manifest.tumblers.groups):
                base = pygame.transform.smoothscale(library.surface(orientation.images[metal]), size)
                for jammed in (False, True):
                    variant = base
                    if jammed:
                        variant = base.copy()
                        variant.fill(settings.theme.jam_tint, special_flags=pygame.BLEND_RGB_MULT)

                    hover = variant.copy()
                    hover.fill(settings.theme.highlight_tint, special_flags=pygame.BLEND_RGB_ADD)
                    self._tumblers[(group, upper, False, jammed)] = ScaledSprite(variant, anchor)
                    self._tumblers[(group, upper, True, jammed)] = ScaledSprite(hover, anchor)

            shadow = pygame.transform.smoothscale(
                library.surface(orientation.shadow.image),
                self._scaled(orientation.shadow.size),
            )
            shadow.set_alpha(settings.theme.shadow_alpha)
            self._shadows[upper] = ScaledSprite(shadow, self._scaled(orientation.shadow.tip_anchor))

        badge = manifest.badges.master
        badge_surface = pygame.transform.smoothscale(library.surface(badge.image), self._scaled(badge.size))
        badge_surface.set_alpha(settings.theme.badge_alpha)
        self.badge = ScaledSprite(badge_surface, self._scaled(badge.center_anchor))
        self.badge_offset = round(badge.tip_offset_pixels * self.scale_y)

        self._picks: Dict[Tuple[PickShape, bool], ScaledSprite] = {}
        for shape, asset in manifest.picks.items():
            active = pygame.transform.smoothscale(library.surface(asset.image), self._scaled(asset.size))
            idle = active.copy()
            idle.set_alpha(settings.alpha.dimmed)
            pick_anchor = self._scaled(asset.tip_anchor)
            self._picks[(shape, True)] = ScaledSprite(active, pick_anchor)
            self._picks[(shape, False)] = ScaledSprite(idle, pick_anchor)

    def _scaled(self, pair: PixelPair) -> PixelPair:
        return scaled_pair(pair, scale_x=self.scale_x, scale_y=self.scale_y)

    def tumbler(
        self,
        group: int,
        *,
        upper: bool,
        highlighted: bool,
        jammed: bool,
        alpha: Optional[int] = None,
    ) -> ScaledSprite:
        key = (group, upper, highlighted, jammed)
        if alpha is None:
            return self._tumblers[key]

        return self._faded_tumbler(key, alpha)

    def _faded_tumbler(self, key: TumblerKey, alpha: int) -> ScaledSprite:
        cached = self._faded.get((key, alpha))
        if cached is None:
            sprite = self._tumblers[key]
            surface = sprite.surface.copy()
            surface.set_alpha(alpha)
            cached = ScaledSprite(surface, sprite.anchor)
            self._faded[(key, alpha)] = cached

        return cached

    def shadow(self, *, upper: bool) -> ScaledSprite:
        return self._shadows[upper]

    def pick(self, shape: PickShape, *, active: bool) -> ScaledSprite:
        return self._picks[(shape, active)]
