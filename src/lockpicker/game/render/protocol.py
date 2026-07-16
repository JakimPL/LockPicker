from __future__ import annotations

from typing import Optional, Protocol, Tuple

import pygame

from lockpicker.game.layout import Layout
from lockpicker.tumbler.location import Location
from lockpicker.tumbler.tumbler import Tumbler


class BoardRenderer(Protocol):
    screen: pygame.surface.Surface
    layout: Layout

    def draw_background(self) -> None: ...

    def get_current_height(self, tumbler: Tumbler) -> float: ...

    def get_tumbler_bounds(self, tumbler: Tumbler) -> Tuple[int, int, int, int]: ...

    def is_mouse_hovering_tumbler(
        self,
        tumbler: Tumbler,
        mouse_position: Tuple[int, int],
        bounds: Optional[Tuple[int, int, int, int]] = None,
    ) -> bool: ...

    def draw_tumbler(
        self,
        tumbler: Tumbler,
        bounds: Optional[Tuple[int, int, int, int]] = None,
        *,
        highlighted: bool = False,
        alpha: Optional[int] = None,
    ) -> None: ...

    def draw_picks(self) -> None: ...

    def get_tumbler_x(self, location: Location) -> int: ...

    def get_tumbler_y(self, location: Location, height: float) -> int: ...
