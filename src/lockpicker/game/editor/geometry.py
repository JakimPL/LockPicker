from __future__ import annotations

from typing import Optional

from lockpicker.engine.lock import Lock
from lockpicker.game.input import MouseState
from lockpicker.game.layout import Layout
from lockpicker.tumbler.definition import TumblerDefinition
from lockpicker.tumbler.location import Location
from lockpicker.tumbler.tumbler import Tumbler


class EditorGeometry:
    def __init__(
        self,
        lock: Lock,
        layout: Layout,
        mouse: MouseState,
    ) -> None:
        self.lock = lock
        self.layout = layout
        self.mouse = mouse

    def pointer_location(self) -> Optional[Location]:
        position = self.layout.position_from_x(self.mouse.position[0])
        if position < 0:
            return None

        upper = self.mouse.position[1] < self.layout.screen_height // 2
        return Location(position, upper)

    def calculate_new_height(
        self,
        location: Location,
        *,
        limit: bool = True,
    ) -> int:
        height = self.layout.height_from_y(self.mouse.position[1], location.upper)
        max_height = self.lock.level.max_height
        counter = self.lock.get_tumbler(location.counter)
        if limit and counter is not None:
            max_height -= counter.base_height

        return max(1, min(height, max_height))

    def calculate_difference(self, location: Location) -> int:
        tumbler = self.lock.get_tumbler(location)
        if tumbler is None:
            return 0

        return self.calculate_new_height(location, limit=False) - tumbler.height

    def temp_tumbler(self, location: Location, group: int) -> Tumbler:
        definition = TumblerDefinition(location, group, self.calculate_new_height(location))
        return Tumbler(definition, self.lock.level.max_height)
