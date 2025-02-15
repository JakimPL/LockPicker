import os
from collections import deque
from pathlib import Path
from typing import Callable, Optional, Tuple, Union

import pygame

from lockpicker.constants.gui import (
    ARROW_COLOR,
    ARROW_SIZE,
    ARROW_WIDTH,
    BAR_OFFSET,
    BAR_WIDTH,
    HEIGHT,
    POST_RELEASE_COLOR,
    X_OFFSET,
)
from lockpicker.game.base import BaseGame
from lockpicker.lock import Lock
from lockpicker.tumbler import Tumbler


class Editor(BaseGame):
    def __init__(
        self, screen: pygame.surface.Surface, lock: Lock, path: Union[str, os.PathLike], run_game_callback: Callable
    ):
        super().__init__(screen, lock)
        self.path = Path(path)

        self.dragging_tumbler = None
        self.initial_height = None

        self.binding_initial = None
        self.binding_target = None

        self.run_game_callback = run_game_callback
        self.current_group = 0

        self.undo_history = deque()
        self.redo_history = deque()
        self.save_state()

    def frame(self):
        self.gather_events()
        self.get_mouse_state()
        self.draw()
        self.handle_dragging()
        self.set_mouse_state()

    def draw(self):
        self.draw_background()
        self.draw_tumblers()
        self.draw_transparent_tumbler()
        self.draw_bindings()
        self.draw_binding_arrow()
        pygame.display.flip()

    def save_state(self):
        last_state = self.undo_history[-1] if self.undo_history else None
        state = self.lock.level.serialize()
        if last_state != state:
            self.undo_history.append(state)
            self.redo_history.clear()

    def undo(self):
        if self.undo_history:
            self.reset_selections()
            self.redo_history.append(self.lock.level.serialize())
            state = self.undo_history.pop()
            self.lock.level = self.lock.level.deserialize(state)

    def redo(self):
        if self.redo_history:
            self.reset_selections()
            self.undo_history.append(self.lock.level.serialize())
            state = self.redo_history.pop()
            self.lock.level = self.lock.level.deserialize(state)

    def gather_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.binding_initial is not None:
                        self.handle_binding_key()
                if event.button == 3:
                    self.cancel_binding()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.terminate()
                if event.key == pygame.K_b:
                    self.handle_binding_key()
                if event.key == pygame.K_m:
                    self.set_master_tumbler()
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if event.key == pygame.K_z:
                        self.undo()
                    if event.key == pygame.K_y:
                        self.redo()
                    if event.key == pygame.K_s:
                        self.save_level()
                    if event.key == pygame.K_p:
                        self.run_game_callback()
                        self.highlighted = None
                if event.key == pygame.K_INSERT:
                    self.add_new_tumbler()
                if event.key == pygame.K_DELETE:
                    self.delete_highlighted_tumbler()
                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    self.change_group(event.key - pygame.K_1)

    def add_new_tumbler(self):
        if self.highlighted is None:
            position = (self.mouse_pos[0] - X_OFFSET) // (BAR_WIDTH + BAR_OFFSET)
            if position < 0:
                return

            upper = self.mouse_pos[1] < HEIGHT // 2
            if self.lock.get_tumbler(position, upper) is None:
                height = self.calculate_new_height(position, upper)
                tumbler = self.get_temp_tumbler(position, upper, height)
                self.lock.add_tumbler(tumbler)

            self.save_state()

    def get_temp_tumbler(self, position: int, upper: bool, height: int) -> Tumbler:
        return Tumbler(position, upper, self.current_group, height, self.lock.level.max_height)

    def delete_highlighted_tumbler(self):
        if self.highlighted is not None:
            position, upper = self.highlighted
            tumbler = self.lock.get_tumbler(position, upper)
            self.lock.delete_tumbler(tumbler)
            self.highlighted = None
            self.save_state()

    def set_master_tumbler(self):
        if self.highlighted is not None:
            position, upper = self.highlighted
            tumbler = self.lock.get_tumbler(position, upper)
            group_tumblers = self.lock.get_tumblers_by_group()[tumbler.group]
            for tumb in group_tumblers:
                tumb.master = False

            tumbler.master = True
            self.save_state()

    def change_group(self, group: int):
        self.current_group = group
        if self.highlighted is not None:
            self.lock.get_tumbler(*self.highlighted).group = group

    def handle_binding_key(self):
        if self.binding_initial is None:
            self.start_binding()
        elif self.binding_target is None:
            self.set_binding_target()
        else:
            self.complete_binding()

    def start_binding(self):
        if self.highlighted is not None:
            self.binding_initial = self.highlighted

    def set_binding_target(self):
        if self.highlighted is not None and self.highlighted != self.binding_initial:
            self.binding_target = self.highlighted

    def complete_binding(self):
        if self.binding_initial is not None and self.binding_target is not None:
            initial_pos, initial_up = self.binding_initial
            target_pos, target_up = self.binding_target
            difference = self.calculate_difference(target_pos, target_up)
            self.lock.add_binding(initial_pos, initial_up, target_pos, target_up, difference)
            self.cancel_binding()
            self.save_state()

    def cancel_binding(self):
        self.binding_initial = None
        self.binding_target = None
        self.highlighted = None

    def handle_dragging(self):
        if self.binding_initial is not None:
            return

        if self.mouse_pressed[0]:
            if self.dragging_tumbler is None and self.highlighted is not None:
                self.dragging_tumbler = self.highlighted
            if self.dragging_tumbler is not None:
                position, upper = self.dragging_tumbler
                tumbler = self.lock.get_tumbler(position, upper)
                new_height = self.calculate_new_height(tumbler.position, tumbler.upper)
                tumbler.height = new_height
        elif self.mouse_pressed[2]:
            if self.dragging_tumbler is None and self.highlighted is not None:
                self.dragging_tumbler = self.highlighted
                position, upper = self.dragging_tumbler
                tumbler = self.lock.get_tumbler(position, upper)
                self.initial_height = tumbler.height
            if self.dragging_tumbler is not None:
                position, upper = self.dragging_tumbler
                tumbler = self.lock.get_tumbler(position, upper)
                new_height = self.calculate_new_height(tumbler.position, tumbler.upper, limit=False)
                tumbler.post_release_height = new_height - self.initial_height
        else:
            if self.dragging_tumbler is not None:
                self.save_state()

            self.dragging_tumbler = None
            self.initial_height = None

    def draw_tumblers(self):
        self.highlighted = None
        for position, items in self.lock.get_tumblers_by_position().items():
            for upper, tumbler in items.items():
                if tumbler is not None:
                    bounds = self.get_tumbler_bounds(tumbler)
                    highlighted = self.is_mouse_hovering_tumbler(tumbler, bounds) and self.dragging_tumbler is None
                    highlighted |= self.dragging_tumbler == (position, upper)
                    if highlighted:
                        self.highlighted = position, upper

                    highlighted |= self.binding_initial == (position, upper)
                    highlighted |= self.binding_target == (position, upper)
                    self.draw_tumbler(tumbler, bounds, highlighted)

    def draw_transparent_tumbler(self):
        position = (self.mouse_pos[0] - X_OFFSET) // (BAR_WIDTH + BAR_OFFSET)
        if position < 0 or self.binding_initial is not None or self.dragging_tumbler is not None:
            return

        upper = self.mouse_pos[1] < HEIGHT // 2
        if self.lock.get_tumbler(position, upper) is None:
            height = self.calculate_new_height(position, upper)
            tumbler = self.get_temp_tumbler(position, upper, height)
            bounds = self.get_tumbler_bounds(tumbler)
            self.draw_tumbler(tumbler, bounds, highlighted=False, alpha=64)

    def draw_tumbler(
        self,
        tumbler: Tumbler,
        bounds: Optional[Tuple[int, int, int, int]] = None,
        highlighted: bool = False,
        alpha: Optional[int] = None,
    ):
        super().draw_tumbler(tumbler, bounds, highlighted, alpha)
        self.draw_post_release_height(tumbler, alpha)

    def draw_post_release_height(self, tumbler: Tumbler, alpha: Optional[int] = None):
        alpha = 160 if alpha is None else alpha
        if tumbler.post_release_height != 0:
            p = tumbler.post_release_height * self.scale
            x = tumbler.position * (BAR_WIDTH + BAR_OFFSET) + X_OFFSET
            height = self.get_current_height(tumbler)
            if tumbler.upper:
                h = height * self.scale
                y = h
            else:
                h = height * self.scale
                y = HEIGHT - h - p

            if p > 0:
                post_release_rect = pygame.Rect(x, y, BAR_WIDTH, p)
            else:
                post_release_rect = pygame.Rect(x, y + p, BAR_WIDTH, -p)

            post_release_surface = pygame.Surface((post_release_rect.width, post_release_rect.height), pygame.SRCALPHA)
            post_release_surface.fill((*POST_RELEASE_COLOR, alpha))
            self.screen.blit(post_release_surface, post_release_rect.topleft)

    def draw_bindings(self):
        for (start_pos, start_up), targets in self.lock.level.bindings.items():
            start_tumbler = self.lock.get_tumbler(start_pos, start_up)
            start_x = self.get_tumbler_x(start_pos)
            start_y = self.get_tumbler_y(start_up, start_tumbler.height)

            for (end_pos, end_up), difference in targets.items():
                end_tumbler = self.lock.get_tumbler(end_pos, end_up)
                intermediate_y = self.get_tumbler_y(end_up, end_tumbler.height)
                end_x = self.get_tumbler_x(end_pos)
                end_y = intermediate_y + self.scale * (difference if end_up else -difference)
                alpha = 255 if self.is_tumbler_bound(start_pos, start_up, end_pos, end_up) else None
                self.draw_arrow(start_x, start_y, intermediate_y, end_x, end_y, alpha=alpha)

    def draw_binding_arrow(self):
        if self.binding_target is not None or self.binding_initial is not None and self.highlighted is not None:
            start_pos, start_up = self.binding_initial
            start_tumbler = self.lock.get_tumbler(start_pos, start_up)
            start_x = self.get_tumbler_x(start_pos)
            start_y = self.get_tumbler_y(start_up, start_tumbler.height)

            end_pos, end_up = self.binding_target if self.binding_target is not None else self.highlighted
            end_tumbler = self.lock.get_tumbler(end_pos, end_up)

            end_x = self.get_tumbler_x(end_pos)
            end_y = self.get_tumbler_y(end_up, end_tumbler.height)
            alpha = 255 if self.is_tumbler_bound(start_pos, start_up, end_pos, end_up) else None
            if self.binding_target is None:
                self.draw_arrow(start_x, start_y, end_y, end_x, end_y, alpha=alpha)
            else:
                intermediate_y = end_y
                difference = self.calculate_difference(end_pos, end_up)
                end_y += difference * self.scale if end_up else -difference * self.scale
                self.draw_arrow(start_x, start_y, intermediate_y, end_x, end_y, alpha=255)

    def draw_arrow(
        self, start_x: int, start_y: int, intermediate_y: int, end_x: int, end_y: int, alpha: Optional[int] = None
    ):
        alpha = 64 if alpha is None else alpha
        if start_x == end_x and start_y == intermediate_y:
            return

        color = (*ARROW_COLOR, alpha)
        surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        pygame.draw.line(surface, color, (start_x, start_y), (end_x, intermediate_y), ARROW_WIDTH)
        pygame.draw.line(surface, color, (end_x, intermediate_y), (end_x, end_y), ARROW_WIDTH)
        pygame.draw.line(surface, color, (end_x - ARROW_SIZE, end_y), (end_x + ARROW_SIZE, end_y), ARROW_WIDTH)
        self.screen.blit(surface, (0, 0))

    def calculate_difference(self, position: int, upper: bool) -> int:
        tumbler = self.lock.get_tumbler(position, upper)
        return self.calculate_new_height(position, upper, limit=False) - tumbler.height

    def calculate_new_height(self, position: int, upper: bool, limit: bool = True) -> int:
        if upper:
            height = round(self.mouse_pos[1] / self.scale)
        else:
            height = round((HEIGHT - self.mouse_pos[1]) / self.scale)

        max_height = self.lock.level.max_height
        counter = self.lock.get_tumbler(position, not upper)
        if limit and counter is not None:
            max_height -= counter.base_height

        return max(1, min(height, max_height))

    def is_tumbler_bound(self, start_pos: int, start_up: bool, end_pos: int, end_up: bool):
        if self.binding_initial is not None:
            target = self.binding_target if self.binding_target is not None else self.highlighted
            highlighted = (start_pos, start_up) == self.binding_initial and (end_pos, end_up) == target
        else:
            highlighted = (start_pos, start_up) == self.highlighted or (end_pos, end_up) == self.highlighted

        return highlighted

    def reset_selections(self):
        self.highlighted = None
        self.binding_initial = None
        self.binding_target = None
        self.dragging_tumbler = None
        self.initial_height = None

    def save_level(self):
        self.lock.level.save(self.path)
