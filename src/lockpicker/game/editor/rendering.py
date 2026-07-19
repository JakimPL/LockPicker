from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import pygame

from lockpicker.constants.config import settings
from lockpicker.engine.lock import Lock
from lockpicker.game.editor.geometry import EditorGeometry
from lockpicker.game.editor.state import EditorState
from lockpicker.game.input import MouseState
from lockpicker.game.render.protocol import BoardRenderer
from lockpicker.tumbler.location import Location
from lockpicker.tumbler.tumbler import Tumbler


@dataclass(frozen=True)
class _ArrowGeometry:
    start_x: float
    start_y: float
    intermediate_y: float
    end_x: float
    end_y: float


class EditorRenderer:
    def __init__(
        self,
        renderer: BoardRenderer,
        lock: Lock,
        state: EditorState,
        geometry: EditorGeometry,
        mouse: MouseState,
    ) -> None:
        self.renderer = renderer
        self.lock = lock
        self.state = state
        self.geometry = geometry
        self.mouse = mouse

    def draw(self) -> None:
        self.renderer.draw_background()
        self.draw_tumblers()
        self.draw_transparent_tumbler()
        self.renderer.draw_frame()
        self.renderer.draw_shear_lips()
        self.draw_bindings()
        self.draw_binding_arrow()
        pygame.display.flip()

    def draw_tumblers(self) -> None:
        self.state.highlighted = None
        for location, tumbler in self.lock.get_tumblers_by_location().items():
            bounds = self.renderer.get_tumbler_bounds(tumbler)
            hovering = self.renderer.is_mouse_hovering_tumbler(tumbler, self.mouse.position, bounds)
            highlighted = hovering and self.state.dragging_tumbler is None
            highlighted |= self.state.dragging_tumbler == location
            if highlighted:
                self.state.highlighted = location

            highlighted |= self.state.binding_initial == location
            highlighted |= self.state.binding_target == location
            self.draw_tumbler(tumbler, bounds, highlighted=highlighted)

    def draw_tumbler(
        self,
        tumbler: Tumbler,
        bounds: Optional[Tuple[int, int, int, int]] = None,
        *,
        highlighted: bool = False,
        alpha: Optional[int] = None,
    ) -> None:
        self.renderer.draw_tumbler(tumbler, bounds, highlighted=highlighted, alpha=alpha)
        self.draw_post_release_height(tumbler, alpha)

    def draw_post_release_height(self, tumbler: Tumbler, alpha: Optional[int] = None) -> None:
        if tumbler.post_release_height == 0:
            return

        alpha = settings.alpha.dimmed if alpha is None else alpha
        rect = self.get_post_release_rect(tumbler)
        surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surface.fill((*settings.color.post_release, alpha))
        self.renderer.screen.blit(surface, rect.topleft)

    def get_post_release_rect(self, tumbler: Tumbler) -> pygame.Rect:
        layout = self.renderer.layout
        post_release_pixels = tumbler.post_release_height * layout.scale
        left = layout.bar_x(tumbler.position)
        height_pixels = self.renderer.get_current_height(tumbler) * layout.scale
        top = height_pixels if tumbler.upper else layout.screen_height - height_pixels - post_release_pixels
        if post_release_pixels > 0:
            return pygame.Rect(left, top, layout.bar_width, post_release_pixels)

        return pygame.Rect(
            left,
            top + post_release_pixels,
            layout.bar_width,
            -post_release_pixels,
        )

    def draw_transparent_tumbler(self) -> None:
        if self.state.binding_initial is not None or self.state.dragging_tumbler is not None:
            return

        location = self.geometry.pointer_location()
        if location is None:
            return

        if self.lock.get_tumbler(location) is None:
            tumbler = self.geometry.temp_tumbler(location, self.state.current_group)
            bounds = self.renderer.get_tumbler_bounds(tumbler)
            self.draw_tumbler(tumbler, bounds, highlighted=False, alpha=settings.alpha.faint)

    def draw_bindings(self) -> None:
        for start_location, targets in self.lock.level.bindings.items():
            start_tumbler = self.lock.get_tumbler(start_location)
            if start_tumbler is None:
                continue

            for end_location, difference in targets.items():
                end_tumbler = self.lock.get_tumbler(end_location)
                if end_tumbler is None:
                    continue

                geometry = self._arrow_geometry(
                    start_location,
                    end_location,
                    start_height=start_tumbler.height,
                    end_height=end_tumbler.height,
                    difference=difference,
                )
                alpha = settings.alpha.opaque if self.is_tumbler_bound(start_location, end_location) else None
                self._draw_arrow_geometry(geometry, alpha=alpha)

    def draw_binding_arrow(self) -> None:
        initial = self.state.binding_initial
        if initial is None:
            return

        end_location = self.state.binding_target if self.state.binding_target is not None else self.state.highlighted
        if end_location is None:
            return

        start_tumbler = self.lock.get_tumbler(initial)
        end_tumbler = self.lock.get_tumbler(end_location)
        if start_tumbler is None or end_tumbler is None:
            return

        if self.state.binding_target is None:
            difference = 0
            alpha = settings.alpha.opaque if self.is_tumbler_bound(initial, end_location) else None
        else:
            difference = self.geometry.calculate_difference(end_location)
            alpha = settings.alpha.opaque

        geometry = self._arrow_geometry(
            initial,
            end_location,
            start_height=start_tumbler.height,
            end_height=end_tumbler.height,
            difference=difference,
        )
        self._draw_arrow_geometry(geometry, alpha=alpha)

    def _arrow_geometry(
        self,
        start_location: Location,
        end_location: Location,
        *,
        start_height: int,
        end_height: int,
        difference: int,
    ) -> _ArrowGeometry:
        intermediate_y = self.renderer.get_tumbler_y(end_location, end_height)
        end_y = intermediate_y + self.renderer.layout.scale * (difference if end_location.upper else -difference)
        return _ArrowGeometry(
            start_x=self.renderer.get_tumbler_x(start_location),
            start_y=self.renderer.get_tumbler_y(start_location, start_height),
            intermediate_y=intermediate_y,
            end_x=self.renderer.get_tumbler_x(end_location),
            end_y=end_y,
        )

    def _draw_arrow_geometry(self, geometry: _ArrowGeometry, *, alpha: Optional[int]) -> None:
        self.draw_arrow(
            start_x=geometry.start_x,
            start_y=geometry.start_y,
            intermediate_y=geometry.intermediate_y,
            end_x=geometry.end_x,
            end_y=geometry.end_y,
            alpha=alpha,
        )

    def draw_arrow(
        self,
        *,
        start_x: float,
        start_y: float,
        intermediate_y: float,
        end_x: float,
        end_y: float,
        alpha: Optional[int] = None,
    ) -> None:
        alpha = settings.alpha.faint if alpha is None else alpha
        if start_x == end_x and start_y == intermediate_y:
            return

        layout = self.renderer.layout
        size = layout.px(settings.arrow.size)
        width = max(1, layout.px(settings.arrow.width))
        color = (*settings.color.arrow, alpha)
        surface = pygame.Surface(self.renderer.screen.get_size(), pygame.SRCALPHA)
        pygame.draw.line(
            surface,
            color,
            (start_x, start_y),
            (end_x, intermediate_y),
            width,
        )
        pygame.draw.line(
            surface,
            color,
            (end_x, intermediate_y),
            (end_x, end_y),
            width,
        )
        pygame.draw.line(
            surface,
            color,
            (end_x - size, end_y),
            (end_x + size, end_y),
            width,
        )
        self.renderer.screen.blit(surface, (0, 0))

    def is_tumbler_bound(self, start_location: Location, end_location: Location) -> bool:
        if self.state.binding_initial is not None:
            target = self.state.binding_target if self.state.binding_target is not None else self.state.highlighted
            highlighted = start_location == self.state.binding_initial and end_location == target
        else:
            highlighted = start_location == self.state.highlighted or end_location == self.state.highlighted

        return highlighted
