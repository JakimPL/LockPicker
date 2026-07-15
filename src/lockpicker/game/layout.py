from __future__ import annotations

from typing import Tuple

from lockpicker.constants.config import settings
from lockpicker.tumbler.location import Location


class Layout:
    def __init__(self, max_height: int) -> None:
        self.max_height = max_height
        self.scale = (settings.screen.height - settings.layout.bar_y_offset) / max_height

    def bar_x(self, position: int) -> int:
        return position * (settings.layout.bar_width + settings.layout.bar_offset) + settings.layout.x_offset

    def center_x(self, position: int) -> int:
        return self.bar_x(position) + settings.layout.bar_width // 2

    def height_to_pixels(self, height: float) -> int:
        return int(height * self.scale)

    def bar_bounds(self, location: Location, height: float) -> Tuple[int, int, int, int]:
        x = self.bar_x(location.position)
        h = self.height_to_pixels(height)
        y = 0 if location.upper else settings.screen.height - h
        return x, y, settings.layout.bar_width, h

    def tip_y(self, location: Location, height: float) -> int:
        h = self.height_to_pixels(height)
        return h if location.upper else settings.screen.height - h

    def position_from_x(self, x: int) -> int:
        return (x - settings.layout.x_offset) // (settings.layout.bar_width + settings.layout.bar_offset)

    def height_from_y(self, y: int, upper: bool) -> int:
        if upper:
            return round(y / self.scale)

        return round((settings.screen.height - y) / self.scale)
