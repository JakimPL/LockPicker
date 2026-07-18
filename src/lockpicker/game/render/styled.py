from __future__ import annotations

from typing import Optional, Tuple

import pygame

from lockpicker.constants.config import settings
from lockpicker.engine.lock import Lock
from lockpicker.game.animation import Animation
from lockpicker.game.assets.sprites import ScaledSprite, ThemeSprites
from lockpicker.game.effects import LipEffects
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
        effects: LipEffects,
        sprites: ThemeSprites,
    ) -> None:
        super().__init__(screen, lock, layout, animation, effects)
        self.sprites = sprites

    def draw_background(self) -> None:
        self.screen.blit(self.sprites.background, (0, 0))
        for tumbler in self.lock.get_tumblers_by_location().values():
            self.blit_anchored(self.sprites.shadow(upper=tumbler.upper), self.get_tip_target(tumbler))

    def draw_tumbler(
        self,
        tumbler: Tumbler,
        bounds: Optional[Tuple[int, int, int, int]] = None,
        *,
        highlighted: bool = False,
        alpha: Optional[int] = None,
    ) -> None:
        sprite = self.sprites.tumbler(
            tumbler.group,
            upper=tumbler.upper,
            highlighted=highlighted,
            jammed=tumbler.jammed,
            alpha=alpha,
        )
        target = self.get_tip_target(tumbler)
        self.blit_anchored(sprite, target)
        if tumbler.master:
            self.draw_badge(tumbler, target)

    def draw_badge(self, tumbler: Tumbler, tip: Tuple[int, int]) -> None:
        offset = -self.sprites.badge_offset if tumbler.upper else self.sprites.badge_offset
        self.blit_anchored(self.sprites.badge, (tip[0], tip[1] + offset))

    def get_tip_target(self, tumbler: Tumbler) -> Tuple[int, int]:
        height = self.get_current_height(tumbler)
        return self.layout.center_x(tumbler.position), self.layout.tip_y(tumbler.location, height)

    def draw_frame(self) -> None:
        self.screen.blit(self.sprites.frame, (0, 0))

    def draw_shear_lips(self) -> None:
        flourish = self.effects.flourish_strength
        for upper in (True, False):
            sprite = self.sprites.lip(upper=upper)
            top = self.layout.shear_line_y(upper=upper) - sprite.anchor[1]
            self.screen.blit(sprite.surface, (0, top))

            glint = self.sprites.lip_glint(upper=upper)
            margin = round(self.layout.bar_pitch) - self.layout.bar_width
            for position, strength in self.effects.glints(upper=upper):
                left = self.layout.bar_x(position) - margin
                width = self.layout.bar_width + 2 * margin
                area = pygame.Rect(left, 0, width, glint.surface.get_height())
                glint.surface.set_alpha(round(255 * strength))
                self.screen.blit(glint.surface, (left, top), area)

            if flourish > 0.0:
                glint.surface.set_alpha(round(255 * flourish))
                self.screen.blit(glint.surface, (0, top))

    def draw_picks(self) -> None:
        for pick in range(self.lock.level.number_of_picks):
            self.draw_pick(pick)

    def draw_pick(self, pick: int) -> None:
        sprite = self.sprites.pick(settings.pick.shapes[pick], active=pick == self.lock.current_pick)
        self.blit_anchored(sprite, self.get_pick_position(pick))

    def blit_anchored(self, sprite: ScaledSprite, target: Tuple[float, float]) -> None:
        left = round(target[0]) - sprite.anchor[0]
        top = round(target[1]) - sprite.anchor[1]
        self.screen.blit(sprite.surface, (left, top))
