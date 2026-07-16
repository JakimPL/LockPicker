from __future__ import annotations

from typing import Optional, Tuple

import pygame
from lockpicker.constants.config import PickShape, settings
from lockpicker.game.render.base import RendererBase
from lockpicker.tumbler.tumbler import Tumbler


class FlatRenderer(RendererBase):
    def draw_background(self) -> None:
        self.screen.fill(settings.color.background)

    def draw_tumbler(
        self,
        tumbler: Tumbler,
        bounds: Optional[Tuple[int, int, int, int]] = None,
        *,
        highlighted: bool = False,
        alpha: Optional[int] = None,
    ) -> None:
        if alpha is None:
            alpha = settings.alpha.opaque if tumbler.master else settings.alpha.dimmed
            alpha //= settings.alpha.jam_divisor if tumbler.jammed else 1

        color = settings.color.highlight if highlighted else settings.color.tumblers[tumbler.group]
        rect = pygame.Rect(*self.get_tumbler_bounds(tumbler) if bounds is None else bounds)
        surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surface.fill((*color, alpha))
        self.screen.blit(surface, rect.topleft)

    def draw_picks(self) -> None:
        for pick in range(self.lock.level.number_of_picks):
            self.draw_pick(pick)

    def draw_pick(self, pick: int) -> None:
        location = self.lock.get_pick(pick)
        alpha = settings.alpha.opaque if pick == self.lock.current_pick else settings.alpha.dimmed
        x, y = self.get_pick_anchor(pick, location)
        self.draw_pick_shape(pick, x, y, alpha)

    def draw_pick_shape(self, pick: int, x: int, y: float, alpha: int) -> None:
        color = (*settings.color.picks[pick], alpha)
        shape_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        size = self.layout.px(settings.pick.size)
        width = max(1, self.layout.px(settings.pick.width))

        match settings.pick.shapes[pick]:
            case PickShape.DIAMOND:
                points = [
                    (x, y - size),
                    (x - size, y),
                    (x, y + size),
                    (x + size, y),
                ]
                pygame.draw.polygon(shape_surface, color, points)
            case PickShape.CIRCLE:
                pygame.draw.circle(shape_surface, color, (x, y), size)

        rect = pygame.Rect(0, y - width // 2, x, width)
        pygame.draw.rect(shape_surface, color, rect)
        self.screen.blit(shape_surface, (0, 0))
