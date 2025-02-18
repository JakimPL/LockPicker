from collections import deque
from typing import Deque

import pygame

from lockpicker.constants.gui import ANIMATION_SPEED
from lockpicker.game.base import BaseGame
from lockpicker.lock import Lock
from lockpicker.state.state import State


class Game(BaseGame):
    def __init__(self, screen: pygame.surface.Surface, lock: Lock, random_moves: bool = False):
        super().__init__(screen, lock)
        self.win = False
        self.loss = False
        self.random_moves = random_moves

        self.undo_history: Deque[State] = deque()
        self.redo_history: Deque[State] = deque()
        self.save_state()

    def frame(self):
        self.gather_events()
        self.get_mouse_state()
        self.draw()
        self.action()
        self.set_mouse_state()
        self.check_win()

    def draw(self):
        self.draw_background()
        self.draw_tumblers()
        self.draw_picks()
        pygame.display.flip()

    def action(self):
        self.toggle_current_pick()
        if not self.animation_frame():
            self.handle_selected_tumbler()
            if self.random_moves:
                self.lock.play_random_move()
            self.animation_items = self.lock.get_recent_changes()

    def animation_frame(self) -> bool:
        if self.animation_items or self.current_animation_item:
            self.animation += ANIMATION_SPEED
            if self.current_animation_item and self.animation >= self.get_max_animation_value():
                self.current_animation_item = {}

            if self.animation_items and not self.current_animation_item:
                self.current_animation_item = self.animation_items.pop()
                self.animation = 0.0

            return True

        return False

    def get_max_animation_value(self) -> int:
        return max(abs(end - start) for start, end in self.current_animation_item.values())

    def handle_selected_tumbler(self):
        if self.mouse_pressed[0] and not self.mouse_was_pressed[0]:
            if self.highlighted is not None:
                self.lock.push(self.highlighted)
            else:
                self.lock.release_current_pick()

            self.save_state()

    def toggle_current_pick(self):
        if self.mouse_pressed[2] and not self.mouse_was_pressed[2]:
            self.lock.change_current_pick()

    def check_win(self) -> bool:
        if self.lock.check_win():
            self.win = True
            self.running = False
            return True
        return False

    def save_state(self):
        last_state = self.undo_history[-1] if self.undo_history else None
        state = self.lock.get_state()
        if last_state != state:
            self.undo_history.append(state)
            self.redo_history.clear()

    def undo(self):
        if self.undo_history:
            self.reset_animation()
            self.redo_history.append(self.lock.get_state())
            state = self.undo_history.pop()
            self.lock.load_state(state)

    def redo(self):
        if self.redo_history:
            self.reset_animation()
            self.undo_history.append(self.lock.get_state())
            state = self.redo_history.pop()
            self.lock.load_state(state)
