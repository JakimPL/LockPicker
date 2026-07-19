from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import pygame

from lockpicker.constants.config import Color, PickShape, settings
from lockpicker.game.assets.library import AssetLibrary
from lockpicker.game.assets.manifest import PixelPair, SpriteAsset, TumblerOrientationAssets
from lockpicker.game.layout import Layout


@dataclass(frozen=True)
class ScaledSprite:
    surface: pygame.surface.Surface
    anchor: PixelPair


def scaled_pair(pair: PixelPair, *, scale_x: float, scale_y: float) -> PixelPair:
    return round(pair[0] * scale_x), round(pair[1] * scale_y)


TumblerKey = Tuple[int, bool, bool, bool]
TumblerState = Tuple[bool, bool]


class ThemeSprites:
    def __init__(self, library: AssetLibrary, layout: Layout) -> None:
        self._library = library
        self._layout = layout
        self._manifest = library.manifest
        self.scale_x = layout.bar_width / self._manifest.tumblers.column_width_pixels
        self.scale_y = layout.scale / self._manifest.tumblers.pixels_per_height_unit

        self.background = self._scale_board(self._manifest.board.background)
        self.frame = self._scale_board(self._manifest.board.frame)

        self._tumblers = self._build_tumblers()
        self._shadows = self._build_shadows()
        self._faded: Dict[Tuple[TumblerKey, int], ScaledSprite] = {}
        self._lips, self._lip_glints = self._build_lips()
        self.badge, self.badge_offset = self._build_badge()
        self._picks = self._build_picks()

    def _scaled(self, pair: PixelPair) -> PixelPair:
        return scaled_pair(pair, scale_x=self.scale_x, scale_y=self.scale_y)

    def _smoothscale(self, image: str, size: PixelPair) -> pygame.surface.Surface:
        return pygame.transform.smoothscale(self._library.surface(image), size)

    def _scale_board(self, image: str) -> pygame.surface.Surface:
        screen_size = (self._layout.screen_width, self._layout.screen_height)
        return pygame.transform.smoothscale(self._library.surface(image), screen_size)

    @staticmethod
    def _tint(surface: pygame.surface.Surface, tint: Color, *, blend: int) -> pygame.surface.Surface:
        tinted = surface.copy()
        tinted.fill(tint, special_flags=blend)
        return tinted

    def _orientations(self) -> Tuple[Tuple[bool, TumblerOrientationAssets], Tuple[bool, TumblerOrientationAssets]]:
        tumblers = self._manifest.tumblers
        return (True, tumblers.upper), (False, tumblers.lower)

    def _build_tumblers(self) -> Dict[TumblerKey, ScaledSprite]:
        tumblers: Dict[TumblerKey, ScaledSprite] = {}
        for upper, orientation in self._orientations():
            size = self._scaled(orientation.size)
            anchor = self._scaled(orientation.tip_anchor)
            for group, metal in enumerate(self._manifest.tumblers.groups):
                base = self._smoothscale(orientation.images[metal], size)
                for (highlighted, jammed), sprite in self._tumbler_states(base, anchor).items():
                    tumblers[(group, upper, highlighted, jammed)] = sprite

        return tumblers

    def _tumbler_states(self, base: pygame.surface.Surface, anchor: PixelPair) -> Dict[TumblerState, ScaledSprite]:
        states: Dict[TumblerState, ScaledSprite] = {}
        for jammed in (False, True):
            variant = base if not jammed else self._tint(base, settings.theme.jam_tint, blend=pygame.BLEND_RGB_MULT)
            highlighted = self._tint(variant, settings.theme.highlight_tint, blend=pygame.BLEND_RGB_ADD)
            states[(False, jammed)] = ScaledSprite(variant, anchor)
            states[(True, jammed)] = ScaledSprite(highlighted, anchor)

        return states

    def _build_shadows(self) -> Dict[bool, ScaledSprite]:
        shadows: Dict[bool, ScaledSprite] = {}
        for upper, orientation in self._orientations():
            shadow = self._smoothscale(orientation.shadow.image, self._scaled(orientation.shadow.size))
            shadow.set_alpha(settings.theme.shadow_alpha)
            shadows[upper] = ScaledSprite(shadow, self._scaled(orientation.shadow.tip_anchor))

        return shadows

    def _build_lips(self) -> Tuple[Dict[bool, ScaledSprite], Dict[bool, ScaledSprite]]:
        lips: Dict[bool, ScaledSprite] = {}
        glints: Dict[bool, ScaledSprite] = {}
        for upper, lip_asset in ((True, self._manifest.lips.upper), (False, self._manifest.lips.lower)):
            lip = self._scale_lip(lip_asset)
            lips[upper] = lip
            glint = self._tint(lip.surface, settings.theme.lip_glint_tint, blend=pygame.BLEND_RGB_ADD)
            glints[upper] = ScaledSprite(glint, lip.anchor)

        return lips, glints

    def _scale_lip(self, lip_asset: SpriteAsset) -> ScaledSprite:
        screen_width = self._layout.screen_width
        size = (screen_width, max(1, round(lip_asset.size[1] * self.scale_y)))
        surface = self._smoothscale(lip_asset.image, size)
        anchor = (
            round(lip_asset.tip_anchor[0] * screen_width / lip_asset.size[0]),
            round(lip_asset.tip_anchor[1] * self.scale_y),
        )
        return ScaledSprite(surface, anchor)

    def _build_badge(self) -> Tuple[ScaledSprite, int]:
        badge = self._manifest.badges.master
        surface = self._smoothscale(badge.image, self._scaled(badge.size))
        surface.set_alpha(settings.theme.badge_alpha)
        sprite = ScaledSprite(surface, self._scaled(badge.center_anchor))
        offset = round(badge.tip_offset_pixels * self.scale_y)
        return sprite, offset

    def _build_picks(self) -> Dict[Tuple[PickShape, bool], ScaledSprite]:
        picks: Dict[Tuple[PickShape, bool], ScaledSprite] = {}
        for shape, asset in self._manifest.picks.items():
            anchor = self._scaled(asset.tip_anchor)
            idle = self._smoothscale(asset.image, self._scaled(asset.size))
            active = self._tint(idle, settings.theme.pick_active_tint, blend=pygame.BLEND_RGB_ADD)
            idle.set_alpha(settings.theme.pick_idle_alpha)
            picks[(shape, True)] = ScaledSprite(active, anchor)
            picks[(shape, False)] = ScaledSprite(idle, anchor)

        return picks

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

    def lip(self, *, upper: bool) -> ScaledSprite:
        return self._lips[upper]

    def lip_glint(self, *, upper: bool) -> ScaledSprite:
        return self._lip_glints[upper]

    def pick(self, shape: PickShape, *, active: bool) -> ScaledSprite:
        return self._picks[(shape, active)]
