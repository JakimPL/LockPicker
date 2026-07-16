from __future__ import annotations

from typing import Tuple

from lockpicker.constants.config import settings
from lockpicker.tumbler.location import Location


class Layout:
    def __init__(self, max_height: int, ui_scale: float = 1.0) -> None:
        self.max_height = max_height
        self.rescale(ui_scale)

    def rescale(self, ui_scale: float) -> None:
        self.ui_scale = ui_scale
        self.screen_width = round(settings.screen.width * ui_scale)
        self.screen_height = round(settings.screen.height * ui_scale)
        self.bar_width = round(settings.layout.bar_width * ui_scale)
        self.bar_pitch = (settings.layout.bar_width + settings.layout.bar_offset) * ui_scale
        self.x_offset = settings.layout.x_offset * ui_scale
        self.scale = (self.screen_height - settings.layout.bar_y_offset * ui_scale) / self.max_height

    def px(self, value: float) -> int:
        return round(value * self.ui_scale)

    def bar_x(self, position: int) -> int:
        return round(position * self.bar_pitch + self.x_offset)

    def center_x(self, position: int) -> int:
        return self.bar_x(position) + self.bar_width // 2

    def height_to_pixels(self, height: float) -> int:
        return int(height * self.scale)

    def bar_bounds(self, location: Location, height: float) -> Tuple[int, int, int, int]:
        x = self.bar_x(location.position)
        h = self.height_to_pixels(height)
        y = 0 if location.upper else self.screen_height - h
        return x, y, self.bar_width, h

    def tip_y(self, location: Location, height: float) -> int:
        h = self.height_to_pixels(height)
        return h if location.upper else self.screen_height - h

    def position_from_x(self, x: int) -> int:
        return int((x - self.x_offset) // self.bar_pitch)

    def height_from_y(self, y: int, upper: bool) -> int:
        if upper:
            return round(y / self.scale)

        return round((self.screen_height - y) / self.scale)
