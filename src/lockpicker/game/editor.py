import os
from collections import deque
from pathlib import Path
from typing import Callable, Deque, Dict, NamedTuple, Optional, Tuple, Union

import pygame

from lockpicker.constants.config import settings
from lockpicker.game.base import BaseGame
from lockpicker.level.level import Level
from lockpicker.lock import Lock
from lockpicker.tumbler.definition import TumblerDefinition
from lockpicker.tumbler.location import Location
from lockpicker.tumbler.tumbler import Tumbler


class LevelSnapshot(NamedTuple):
    number_of_picks: int
    max_height: int
    tumblers: Dict[Location, TumblerDefinition]
    bindings: Dict[Location, Dict[Location, int]]


class Editor(BaseGame):
    def __init__(
        self,
        screen: pygame.surface.Surface,
        lock: Lock,
        path: Union[str, os.PathLike[str]],
        run_game_callback: Callable[[], None],
    ):
        super().__init__(screen, lock)
        self.path = Path(path)

        self.dragging_tumbler: Optional[Location] = None
        self.initial_height: Optional[int] = None

        self.binding_initial: Optional[Location] = None
        self.binding_target: Optional[Location] = None

        self.run_game_callback = run_game_callback
        self.current_group = 0

        self.undo_history: Deque[LevelSnapshot] = deque()
        self.redo_history: Deque[LevelSnapshot] = deque()
        self.save_state()

    def frame(self) -> None:
        self.gather_events()
        self.get_mouse_state()
        self.draw()
        self.handle_dragging()
        self.set_mouse_state()

    def draw(self) -> None:
        self.draw_background()
        self.draw_tumblers()
        self.draw_transparent_tumbler()
        self.draw_bindings()
        self.draw_binding_arrow()
        pygame.display.flip()

    def capture_snapshot(self) -> LevelSnapshot:
        level = self.lock.level
        tumblers = {location: tumbler.definition for location, tumbler in level.tumblers.items()}
        bindings = {location: dict(targets) for location, targets in level.bindings.items()}
        return LevelSnapshot(level.number_of_picks, level.max_height, tumblers, bindings)

    def restore_snapshot(self, snapshot: LevelSnapshot) -> None:
        tumblers = {
            location: Tumbler(definition, snapshot.max_height) for location, definition in snapshot.tumblers.items()
        }
        bindings = {location: dict(targets) for location, targets in snapshot.bindings.items()}
        self.lock.level = Level(snapshot.number_of_picks, snapshot.max_height, tumblers, bindings)

    def save_state(self) -> None:
        snapshot = self.capture_snapshot()
        last_state = self.undo_history[-1] if self.undo_history else None
        if last_state != snapshot:
            self.undo_history.append(snapshot)
            self.redo_history.clear()

    def undo(self) -> None:
        if self.undo_history:
            self.reset_selections()
            self.redo_history.append(self.capture_snapshot())
            snapshot = self.undo_history.pop()
            self.restore_snapshot(snapshot)

    def redo(self) -> None:
        if self.redo_history:
            self.reset_selections()
            self.undo_history.append(self.capture_snapshot())
            snapshot = self.redo_history.pop()
            self.restore_snapshot(snapshot)

    def gather_events(self) -> None:
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    self.running = False
                case pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_button(event)
                case pygame.KEYDOWN:
                    self.handle_key(event)

    def handle_mouse_button(self, event: pygame.event.Event) -> None:
        match event.button:
            case 1:
                if self.binding_initial is not None:
                    self.handle_binding_key()
            case 3:
                self.cancel_binding()

    def handle_key(self, event: pygame.event.Event) -> None:
        match event.key:
            case pygame.K_ESCAPE:
                self.terminate()
            case pygame.K_b:
                self.handle_binding_key()
            case pygame.K_m:
                self.set_master_tumbler()
            case pygame.K_INSERT:
                self.add_new_tumbler()
            case pygame.K_DELETE:
                self.delete_highlighted_tumbler()
            case pygame.K_1 | pygame.K_2 | pygame.K_3:
                self.change_group(event.key - pygame.K_1)

        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.handle_ctrl_key(event.key)

    def handle_ctrl_key(self, key: int) -> None:
        match key:
            case pygame.K_z:
                self.undo()
            case pygame.K_y:
                self.redo()
            case pygame.K_s:
                self.save_level()
            case pygame.K_p:
                self.run_game_callback()
                self.highlighted = None

    def add_new_tumbler(self) -> None:
        if self.highlighted is None:
            position = self.layout.position_from_x(self.mouse_pos[0])
            if position < 0:
                return

            upper = self.mouse_pos[1] < settings.screen.height // 2
            location = Location(position, upper)
            if self.lock.get_tumbler(location) is None:
                height = self.calculate_new_height(location)
                tumbler = self.get_temp_tumbler(location, height)
                self.lock.level.add_tumbler(tumbler)

            self.save_state()

    def get_temp_tumbler(self, location: Location, height: int) -> Tumbler:
        definition = TumblerDefinition(location, self.current_group, height)
        return Tumbler(definition, self.lock.level.max_height)

    def delete_highlighted_tumbler(self) -> None:
        if self.highlighted is not None:
            tumbler = self.lock.get_tumbler(self.highlighted)
            if tumbler is not None:
                self.lock.level.remove_tumbler(tumbler)

            self.highlighted = None
            self.save_state()

    def set_master_tumbler(self) -> None:
        if self.highlighted is not None:
            self.lock.level.set_master(self.highlighted)
            self.save_state()

    def change_group(self, group: int) -> None:
        self.current_group = group
        if self.highlighted is not None:
            tumbler = self.lock.get_tumbler(self.highlighted)
            if tumbler is not None:
                tumbler.set_group(group)

    def handle_binding_key(self) -> None:
        if self.binding_initial is None:
            self.start_binding()
        elif self.binding_target is None:
            self.set_binding_target()
        else:
            self.complete_binding()

    def start_binding(self) -> None:
        if self.highlighted is not None:
            self.binding_initial = self.highlighted

    def set_binding_target(self) -> None:
        if self.highlighted is not None and self.highlighted != self.binding_initial:
            self.binding_target = self.highlighted

    def complete_binding(self) -> None:
        if self.binding_initial is not None and self.binding_target is not None:
            difference = self.calculate_difference(self.binding_target)
            self.lock.level.add_binding(self.binding_initial, self.binding_target, difference)
            self.cancel_binding()
            self.save_state()

    def cancel_binding(self) -> None:
        self.binding_initial = None
        self.binding_target = None
        self.highlighted = None

    def handle_dragging(self) -> None:
        if self.binding_initial is not None:
            return

        if self.mouse_pressed[0]:
            self.drag_height()
        elif self.mouse_pressed[2]:
            self.drag_post_release_height()
        else:
            self.end_dragging()

    def drag_height(self) -> None:
        if self.dragging_tumbler is None and self.highlighted is not None:
            self.dragging_tumbler = self.highlighted

        if self.dragging_tumbler is not None:
            tumbler = self.lock.get_tumbler(self.dragging_tumbler)
            if tumbler is not None:
                new_height = self.calculate_new_height(self.dragging_tumbler)
                tumbler.set_height(new_height)

    def drag_post_release_height(self) -> None:
        if self.dragging_tumbler is None and self.highlighted is not None:
            self.dragging_tumbler = self.highlighted
            tumbler = self.lock.get_tumbler(self.dragging_tumbler)
            if tumbler is not None:
                self.initial_height = tumbler.height

        if self.dragging_tumbler is not None:
            tumbler = self.lock.get_tumbler(self.dragging_tumbler)
            if tumbler is not None and self.initial_height is not None:
                new_height = self.calculate_new_height(self.dragging_tumbler, limit=False)
                tumbler.set_post_release_height(new_height - self.initial_height)

    def end_dragging(self) -> None:
        if self.dragging_tumbler is not None:
            self.save_state()

        self.dragging_tumbler = None
        self.initial_height = None

    def draw_tumblers(self) -> None:
        self.highlighted = None
        for location, tumbler in self.lock.get_tumblers_by_location().items():
            bounds = self.get_tumbler_bounds(tumbler)
            highlighted = self.is_mouse_hovering_tumbler(tumbler, bounds) and self.dragging_tumbler is None
            highlighted |= self.dragging_tumbler == location
            if highlighted:
                self.highlighted = location

            highlighted |= self.binding_initial == location
            highlighted |= self.binding_target == location
            self.draw_tumbler(tumbler, bounds, highlighted=highlighted)

    def draw_transparent_tumbler(self) -> None:
        position = self.layout.position_from_x(self.mouse_pos[0])
        if position < 0 or self.binding_initial is not None or self.dragging_tumbler is not None:
            return

        upper = self.mouse_pos[1] < settings.screen.height // 2
        location = Location(position, upper)
        if self.lock.get_tumbler(location) is None:
            height = self.calculate_new_height(location)
            tumbler = self.get_temp_tumbler(location, height)
            bounds = self.get_tumbler_bounds(tumbler)
            self.draw_tumbler(tumbler, bounds, highlighted=False, alpha=settings.alpha.faint)

    def draw_tumbler(
        self,
        tumbler: Tumbler,
        bounds: Optional[Tuple[int, int, int, int]] = None,
        *,
        highlighted: bool = False,
        alpha: Optional[int] = None,
    ) -> None:
        super().draw_tumbler(tumbler, bounds, highlighted=highlighted, alpha=alpha)
        self.draw_post_release_height(tumbler, alpha)

    def draw_post_release_height(
        self,
        tumbler: Tumbler,
        alpha: Optional[int] = None,
    ) -> None:
        if tumbler.post_release_height == 0:
            return

        alpha = settings.alpha.dimmed if alpha is None else alpha
        rect = self.get_post_release_rect(tumbler)
        surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surface.fill((*settings.color.post_release, alpha))
        self.screen.blit(surface, rect.topleft)

    def get_post_release_rect(self, tumbler: Tumbler) -> pygame.Rect:
        p = tumbler.post_release_height * self.layout.scale
        x = self.layout.bar_x(tumbler.position)
        h = self.get_current_height(tumbler) * self.layout.scale
        y = h if tumbler.upper else settings.screen.height - h - p
        if p > 0:
            return pygame.Rect(x, y, settings.layout.bar_width, p)

        return pygame.Rect(x, y + p, settings.layout.bar_width, -p)

    def draw_bindings(self) -> None:
        for start_location, targets in self.lock.level.bindings.items():
            start_tumbler = self.lock.get_tumbler(start_location)
            if start_tumbler is None:
                continue

            start_x = self.get_tumbler_x(start_location)
            start_y = self.get_tumbler_y(start_location, start_tumbler.height)

            for end_location, difference in targets.items():
                end_tumbler = self.lock.get_tumbler(end_location)
                if end_tumbler is None:
                    continue

                intermediate_y = self.get_tumbler_y(end_location, end_tumbler.height)
                end_x = self.get_tumbler_x(end_location)
                end_y = intermediate_y + self.layout.scale * (difference if end_location.upper else -difference)
                alpha = settings.alpha.opaque if self.is_tumbler_bound(start_location, end_location) else None
                self.draw_arrow(
                    start_x=start_x,
                    start_y=start_y,
                    intermediate_y=intermediate_y,
                    end_x=end_x,
                    end_y=end_y,
                    alpha=alpha,
                )

    def draw_binding_arrow(self) -> None:
        initial = self.binding_initial
        if initial is None:
            return

        end_location = self.binding_target if self.binding_target is not None else self.highlighted
        if end_location is None:
            return

        start_tumbler = self.lock.get_tumbler(initial)
        end_tumbler = self.lock.get_tumbler(end_location)
        if start_tumbler is None or end_tumbler is None:
            return

        start_x = self.get_tumbler_x(initial)
        start_y = self.get_tumbler_y(initial, start_tumbler.height)
        end_x = self.get_tumbler_x(end_location)
        end_y = self.get_tumbler_y(end_location, end_tumbler.height)

        if self.binding_target is None:
            alpha = settings.alpha.opaque if self.is_tumbler_bound(initial, end_location) else None
            self.draw_arrow(
                start_x=start_x,
                start_y=start_y,
                intermediate_y=end_y,
                end_x=end_x,
                end_y=end_y,
                alpha=alpha,
            )
        else:
            difference = self.calculate_difference(end_location)
            offset = difference * self.layout.scale if end_location.upper else -difference * self.layout.scale
            self.draw_arrow(
                start_x=start_x,
                start_y=start_y,
                intermediate_y=end_y,
                end_x=end_x,
                end_y=end_y + offset,
                alpha=settings.alpha.opaque,
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

        color = (*settings.color.arrow, alpha)
        surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        pygame.draw.line(
            surface,
            color,
            (start_x, start_y),
            (end_x, intermediate_y),
            settings.arrow.width,
        )
        pygame.draw.line(
            surface,
            color,
            (end_x, intermediate_y),
            (end_x, end_y),
            settings.arrow.width,
        )
        pygame.draw.line(
            surface,
            color,
            (end_x - settings.arrow.size, end_y),
            (end_x + settings.arrow.size, end_y),
            settings.arrow.width,
        )
        self.screen.blit(surface, (0, 0))

    def calculate_difference(self, location: Location) -> int:
        tumbler = self.lock.get_tumbler(location)
        if tumbler is None:
            return 0

        return self.calculate_new_height(location, limit=False) - tumbler.height

    def calculate_new_height(
        self,
        location: Location,
        *,
        limit: bool = True,
    ) -> int:
        height = self.layout.height_from_y(self.mouse_pos[1], location.upper)
        max_height = self.lock.level.max_height
        counter = self.lock.get_tumbler(location.counter)
        if limit and counter is not None:
            max_height -= counter.base_height

        return max(1, min(height, max_height))

    def is_tumbler_bound(self, start_location: Location, end_location: Location) -> bool:
        if self.binding_initial is not None:
            target = self.binding_target if self.binding_target is not None else self.highlighted
            highlighted = start_location == self.binding_initial and end_location == target
        else:
            highlighted = start_location == self.highlighted or end_location == self.highlighted

        return highlighted

    def reset_selections(self) -> None:
        self.highlighted = None
        self.binding_initial = None
        self.binding_target = None
        self.dragging_tumbler = None
        self.initial_height = None

    def save_level(self) -> None:
        self.lock.level.save(self.path)
