from __future__ import annotations

from typing import Optional, Tuple

import pygame

from lockpicker.constants.config import settings
from lockpicker.engine.lock import Lock
from lockpicker.game.animation import Animation
from lockpicker.game.assets.sprites import ScaledSprite, ThemeSprites
from lockpicker.game.layout import Layout
from lockpicker.game.render.base import RendererBase
from lockpicker.tumbler.tumbler import Tumbler


class StyledRenderer(RendererBase):
    def __init__(
        self,
        screen: pygame.surface.Surface,
        lock: Lock,
        layout: Layout,
        animation: Animation,
        sprites: ThemeSprites,
    ) -> None:
        super().__init__(screen, lock, layout, animation)
        self.sprites = sprites

    def draw_background(self) -> None:
        self.screen.blit(self.sprites.background, (0, 0))

    def draw_tumbler(
        self,
        tumbler: Tumbler,
        bounds: Optional[Tuple[int, int, int, int]] = None,
        *,
        highlighted: bool = False,
        alpha: Optional[int] = None,
    ) -> None:
        sprite = self.sprites.tumbler(tumbler.group, upper=tumbler.upper, highlighted=highlighted)
        height = self.get_current_height(tumbler)
        target = (self.layout.center_x(tumbler.position), self.layout.tip_y(tumbler.location, height))
        self.blit_anchored(sprite, target)

    def draw_picks(self) -> None:
        self.screen.blit(self.sprites.frame, (0, 0))
        for pick in range(self.lock.level.number_of_picks):
            self.draw_pick(pick)

    def draw_pick(self, pick: int) -> None:
        location = self.lock.get_pick(pick)
        sprite = self.sprites.pick(settings.pick.shapes[pick])
        self.blit_anchored(sprite, self.get_pick_anchor(pick, location))

    def blit_anchored(self, sprite: ScaledSprite, target: Tuple[float, float]) -> None:
        left = round(target[0]) - sprite.anchor[0]
        top = round(target[1]) - sprite.anchor[1]
        self.screen.blit(sprite.surface, (left, top))
