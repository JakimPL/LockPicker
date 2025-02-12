import os
from pathlib import Path
from typing import Union

import pygame

from lockpicker.constants.gui import HEIGHT, SCALE
from lockpicker.game.base import BaseGame
from lockpicker.lock import Lock
from lockpicker.tumbler import Tumbler


class Editor(BaseGame):
    def __init__(self, lock: Lock, path: Union[str, os.PathLike]):
        super().__init__(lock)
        self.path = Path(path)
        self.save_path = self.get_save_path()
        self.dragging_tumbler = None

    def gather_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_s
                and pygame.key.get_mods() & pygame.KMOD_CTRL
            ):
                self.save_level()

    def run(self):
        self.running = True
        while self.running:
            self.frame()
        self.terminate()

    def frame(self):
        self.gather_events()
        self.get_mouse_state()
        self.draw()
        self.handle_dragging()
        self.set_mouse_state()

    def handle_dragging(self):
        if self.mouse_pressed[0]:
            if self.dragging_tumbler is None and self.highlighted is not None:
                self.dragging_tumbler = self.highlighted
            if self.dragging_tumbler is not None:
                position, upper = self.dragging_tumbler
                tumbler = self.lock.positions[position][upper]
                new_height = self.calculate_new_height(tumbler)
                tumbler.height = new_height
        else:
            self.dragging_tumbler = None

    def calculate_new_height(self, tumbler: Tumbler) -> int:
        if tumbler.upper:
            height = self.mouse_pos[1] // SCALE
        else:
            height = (HEIGHT - self.mouse_pos[1]) // SCALE

        return max(1, min(height, self.lock.max_height))

    def draw(self):
        self.draw_background()
        self.draw_tumblers()
        pygame.display.flip()

    def get_save_path(self) -> Path:
        filename = self.path.name + "_edit" + self.path.suffix
        return self.path.parent / filename

    def save_level(self):
        self.lock.level.save(self.save_path)
