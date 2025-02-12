import os
from pathlib import Path
from typing import Callable, Union

import pygame

from lockpicker.constants.gui import (
    BAR_OFFSET,
    BAR_WIDTH,
    HEIGHT,
    POST_RELEASE_COLOR,
    SCALE,
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
        self.save_path = self.get_save_path()

        self.dragging_tumbler = None
        self.initial_height = None

        self.run_game_callback = run_game_callback
        self.current_group = 0

    def frame(self):
        self.gather_events()
        self.get_mouse_state()
        self.draw()
        self.handle_dragging()
        self.set_mouse_state()

    def draw(self):
        self.draw_background()
        self.draw_tumblers()
        pygame.display.flip()

    def gather_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    # if event.key == pygame.K_z:
                    #     self.lock.undo()
                    # if event.key == pygame.K_y:
                    #     self.lock.redo()
                    if event.key == pygame.K_s:
                        self.save_level()
                    if event.key == pygame.K_p:
                        self.run_game_callback()
                    if event.key == pygame.K_m:
                        self.set_master_tumbler()
                if event.key == pygame.K_INSERT:
                    self.add_new_tumbler()
                if event.key == pygame.K_DELETE:
                    self.delete_highlighted_tumbler()

    def add_new_tumbler(self):
        if self.highlighted is None:
            position = (self.mouse_pos[0] - X_OFFSET) // (BAR_WIDTH + BAR_OFFSET)
            if position < 0:
                return

            if position not in self.lock.positions:
                self.lock.positions[position] = {}

            upper = self.mouse_pos[1] < HEIGHT // 2
            if self.lock.positions[position].get(upper) is None:
                new_height = self.calculate_new_height(position, upper)
                new_tumbler = Tumbler(position, upper, self.current_group, new_height)
                self.lock.positions[position][upper] = new_tumbler
                self.lock.tumblers.append(new_tumbler)
                self.lock.groups[self.current_group].append(new_tumbler)

    def delete_highlighted_tumbler(self):
        if self.highlighted is not None:
            position, upper = self.highlighted
            tumbler = self.lock.positions[position][upper]
            self.lock.tumblers.pop(self.lock.tumblers.index(tumbler))
            del self.lock.positions[position][upper]
            del tumbler

            new_rules = {}
            for current, rules in self.lock.rules.items():
                if current == self.highlighted:
                    continue

                pos, up = current
                new_rules[current] = [(p, u, h) for p, u, h in self.lock.rules[current] if p != pos and u != up]

            self.lock.rules = new_rules
            self.highlighted = None

    def set_master_tumbler(self):
        if self.highlighted is not None:
            position, upper = self.highlighted
            tumbler = self.lock.positions[position][upper]
            tumbler.master = True
            for tumb in self.lock.groups[tumbler.group]:
                if tumb is not tumbler:
                    tumb.master = False

    def handle_dragging(self):
        if self.mouse_pressed[0]:
            if self.dragging_tumbler is None and self.highlighted is not None:
                self.dragging_tumbler = self.highlighted
            if self.dragging_tumbler is not None:
                position, upper = self.dragging_tumbler
                tumbler = self.lock.positions[position][upper]
                new_height = self.calculate_new_height(tumbler.position, tumbler.upper)
                tumbler.height = new_height
        elif self.mouse_pressed[2]:
            if self.dragging_tumbler is None and self.highlighted is not None:
                self.dragging_tumbler = self.highlighted
                position, upper = self.dragging_tumbler
                tumbler = self.lock.positions[position][upper]
                self.initial_height = tumbler.height
            if self.dragging_tumbler is not None:
                position, upper = self.dragging_tumbler
                tumbler = self.lock.positions[position][upper]
                new_height = self.calculate_new_height(tumbler.position, tumbler.upper, limit=False)
                tumbler.post_release_height = new_height - self.initial_height
        else:
            self.dragging_tumbler = None
            self.initial_height = None

    def draw_tumbler(self, tumbler: Tumbler, position: int) -> bool:
        collision = super().draw_tumbler(tumbler, position)
        self.draw_post_release_height(tumbler, position)
        return collision

    def draw_post_release_height(self, tumbler: Tumbler, position: int):
        if tumbler.post_release_height != 0:
            p = tumbler.post_release_height * SCALE
            x = position * (BAR_WIDTH + BAR_OFFSET) + X_OFFSET
            height = self.get_current_height(tumbler)
            if tumbler.upper:
                h = height * SCALE
                y = h

            else:
                h = height * SCALE
                y = HEIGHT - h - p

            if p > 0:
                post_release_rect = pygame.Rect(x, y, BAR_WIDTH, p)
            else:
                post_release_rect = pygame.Rect(x, y + p, BAR_WIDTH, -p)

            post_release_surface = pygame.Surface((post_release_rect.width, post_release_rect.height), pygame.SRCALPHA)
            post_release_surface.fill((*POST_RELEASE_COLOR, 160))
            self.screen.blit(post_release_surface, post_release_rect.topleft)

    def calculate_new_height(self, position: int, upper: bool, limit: bool = True) -> int:
        if upper:
            height = self.mouse_pos[1] // SCALE
        else:
            height = (HEIGHT - self.mouse_pos[1]) // SCALE

        max_height = self.lock.max_height
        counter = self.lock.positions[position].get(not upper)
        if limit and counter is not None:
            max_height -= counter.base_height

        return max(1, min(height, max_height))

    def get_save_path(self) -> Path:
        filename = self.path.with_stem(f"{self.path.stem}_edit")
        return self.path.parent / filename

    def save_level(self):
        self.lock.level.save(self.save_path)
