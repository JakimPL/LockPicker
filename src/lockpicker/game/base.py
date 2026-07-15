from typing import List, Optional, Tuple

import pygame

from lockpicker.constants.config import PickShape, settings
from lockpicker.game.animation import AnimationStep
from lockpicker.game.layout import Layout
from lockpicker.lock import Lock
from lockpicker.tumbler.location import Location
from lockpicker.tumbler.tumbler import Tumbler


class BaseGame:
    def __init__(self, screen: pygame.surface.Surface, lock: Lock):
        self.screen = screen
        self.running = False

        self.lock = lock

        self.mouse_pos: Tuple[int, int] = (0, 0)
        self.mouse_pressed: Tuple[bool, ...] = (False, False, False)
        self.mouse_was_pressed: Tuple[bool, ...] = (False, False, False)

        self.highlighted: Optional[Location] = None

        self.animation = 0.0
        self.animation_items: List[AnimationStep] = []
        self.current_animation_item: AnimationStep = {}

        self.layout = Layout(self.lock.level.max_height)

    def run(self) -> None:
        self.running = True
        while self.running:
            self.frame()

    def frame(self) -> None:
        raise NotImplementedError("frame method must be implemented in child class")

    def gather_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.terminate()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.terminate()
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    match event.key:
                        case pygame.K_z:
                            self.undo()
                        case pygame.K_y:
                            self.redo()
                        case pygame.K_r:
                            self.restart()

    def get_mouse_state(self) -> None:
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_pressed = pygame.mouse.get_pressed()

    def set_mouse_state(self) -> None:
        self.mouse_was_pressed = self.mouse_pressed

    def draw_background(self) -> None:
        self.screen.fill(settings.color.background)

    def draw_tumblers(self) -> None:
        self.highlighted = None
        for location, tumbler in self.lock.get_tumblers_by_location().items():
            bounds = self.get_tumbler_bounds(tumbler)
            highlighted = self.is_mouse_hovering_tumbler(tumbler, bounds)
            self.draw_tumbler(tumbler, bounds, highlighted=highlighted)
            if highlighted:
                self.highlighted = location

    def get_tumbler_bounds(self, tumbler: Tumbler) -> Tuple[int, int, int, int]:
        height = self.get_current_height(tumbler)
        return self.layout.bar_bounds(tumbler.location, height)

    def is_mouse_hovering_tumbler(
        self,
        tumbler: Tumbler,
        bounds: Optional[Tuple[int, int, int, int]] = None,
    ) -> bool:
        rect = pygame.Rect(*self.get_tumbler_bounds(tumbler) if bounds is None else bounds)
        return bool(rect.collidepoint(self.mouse_pos))

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

    def get_pick_anchor(self, pick: int, location: Optional[Location]) -> Tuple[int, float]:
        if location is None:
            x = settings.pick.idle_offset
            y = settings.screen.height / 2 + settings.pick.discrepancy * (
                pick - self.lock.level.number_of_picks / 2 + 0.5
            )
            return x, y

        tumbler = self.lock.get_tumbler(location)
        if tumbler is None:
            raise ValueError(f"No tumbler found at location {location}")

        height = self.get_current_height(tumbler)
        h = self.layout.height_to_pixels(height)
        x = self.layout.center_x(location.position)
        y = h + settings.pick.offset if location.upper else settings.screen.height - h - settings.pick.offset
        return x, y

    def draw_pick_shape(self, pick: int, x: int, y: float, alpha: int) -> None:
        color = (*settings.color.picks[pick], alpha)
        shape_surface = pygame.Surface((settings.screen.width, settings.screen.height), pygame.SRCALPHA)

        match settings.pick.shapes[pick]:
            case PickShape.DIAMOND:
                points = [
                    (x, y - settings.pick.size),
                    (x - settings.pick.size, y),
                    (x, y + settings.pick.size),
                    (x + settings.pick.size, y),
                ]
                pygame.draw.polygon(shape_surface, color, points)
            case PickShape.CIRCLE:
                pygame.draw.circle(shape_surface, color, (x, y), settings.pick.size)

        rect = pygame.Rect(0, y - settings.pick.width // 2, x, settings.pick.width)
        pygame.draw.rect(shape_surface, color, rect)
        self.screen.blit(shape_surface, (0, 0))

    def get_tumbler_x(self, location: Location) -> int:
        return self.layout.center_x(location.position)

    def get_tumbler_y(self, location: Location, height: float) -> int:
        return self.layout.tip_y(location, height)

    def get_current_height(self, tumbler: Tumbler) -> float:
        if tumbler.location in self.current_animation_item:
            start, end = self.current_animation_item[tumbler.location]
            if end > start:
                height = start + min(self.animation, end - start)
            else:
                height = start + max(-self.animation, end - start)
        else:
            height = tumbler.height

        return height

    def restart(self) -> None:
        self.lock.reset()
        self.reset_animation()

    def reset_animation(self) -> None:
        self.animation = 0.0
        self.animation_items = []
        self.current_animation_item = {}

    def terminate(self) -> None:
        self.running = False

    def undo(self) -> None:
        raise NotImplementedError("undo method must be implemented in child class")

    def redo(self) -> None:
        raise NotImplementedError("redo method must be implemented in child class")
