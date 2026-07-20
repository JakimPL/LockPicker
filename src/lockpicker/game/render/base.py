from __future__ import annotations

from typing import Optional, Tuple

import pygame

from lockpicker.constants.config import settings
from lockpicker.engine.lock import Lock
from lockpicker.game.animation import Animation
from lockpicker.game.effects import LipEffects
from lockpicker.game.layout import Layout
from lockpicker.tumbler.location import Location
from lockpicker.tumbler.tumbler import Tumbler


class RendererBase:
    def __init__(
        self,
        screen: pygame.surface.Surface,
        lock: Lock,
        layout: Layout,
        animation: Animation,
        effects: LipEffects,
    ) -> None:
        self.screen = screen
        self.lock = lock
        self.layout = layout
        self.animation = animation
        self.effects = effects

    def draw_frame(self) -> None:
        pass

    def draw_shear_lips(self) -> None:
        pass

    def get_current_height(self, tumbler: Tumbler) -> float:
        return self.animation.height(tumbler)

    def get_tumbler_bounds(self, tumbler: Tumbler) -> Tuple[int, int, int, int]:
        height = self.get_current_height(tumbler)
        return self.layout.bar_bounds(tumbler.location, height)

    def is_mouse_hovering_tumbler(
        self,
        tumbler: Tumbler,
        mouse_position: Tuple[int, int],
        bounds: Optional[Tuple[int, int, int, int]] = None,
    ) -> bool:
        rect = pygame.Rect(*self.get_tumbler_bounds(tumbler) if bounds is None else bounds)
        return bool(rect.collidepoint(mouse_position))

    def get_pick_position(self, pick: int) -> Tuple[float, float]:
        change = self.animation.pick_change(pick)
        if change is None:
            return self.get_pick_anchor(pick, self.lock.get_pick(pick))

        progress = self.animation.progress
        start_x, start_y = self.get_pick_anchor(pick, change.start)
        end_x, end_y = self.get_pick_anchor(pick, change.end)
        return start_x + (end_x - start_x) * progress, start_y + (end_y - start_y) * progress

    def get_pick_anchor(self, pick: int, location: Optional[Location]) -> Tuple[int, float]:
        if location is None:
            x = self.layout.px(settings.pick.idle_offset)
            y = self.layout.screen_height / 2 + self.layout.px(settings.pick.discrepancy) * (
                pick - self.lock.level.number_of_picks / 2 + 0.5
            )
            return x, y

        tumbler = self.lock.get_tumbler(location)
        if tumbler is None:
            raise ValueError(f"No tumbler found at location {location}")

        height = self.get_current_height(tumbler)
        h = self.layout.height_to_pixels(height)
        x = self.layout.center_x(location.position)
        offset = self.layout.px(settings.pick.offset)
        y = h + offset if location.upper else self.layout.screen_height - h - offset
        return x, y

    def get_tumbler_x(self, location: Location) -> int:
        return self.layout.center_x(location.position)

    def get_tumbler_y(self, location: Location, height: float) -> int:
        return self.layout.tip_y(location, height)
