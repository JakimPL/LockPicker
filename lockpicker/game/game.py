import random

import pygame

from lockpicker.constants.gui import ANIMATION_SPEED
from lockpicker.game.base import BaseGame
from lockpicker.lock import Lock


class Game(BaseGame):
    def __init__(self, screen: pygame.surface.Surface, lock: Lock, random_moves: bool = False):
        super().__init__(screen, lock)
        self.win = False
        self.loss = False
        self.random_moves = random_moves

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
            self.animation_items = self.lock.get_recent_changes()
            if self.random_moves:
                self.play_random_move()

    def play_random_move(self):
        moves = self.lock.get_possible_moves()
        if moves:
            move = random.choice(moves)
            pick = random.choice(range(self.lock.level.number_of_picks))
            self.lock.select_pick(pick)
            self.lock.push(*move)

    def animation_frame(self) -> bool:
        if self.animation_items:
            self.animation += ANIMATION_SPEED
            if self.animation >= self.get_max_animation_value():
                self.animation = 0.0
                self.animation_items = {}
        return bool(self.animation_items)

    def get_max_animation_value(self) -> int:
        return max(abs(end - start) for start, end in self.animation_items.values())

    def handle_selected_tumbler(self):
        if self.mouse_pressed[0] and not self.mouse_was_pressed[0]:
            self.lock.release_current_pick()
            if self.highlighted is not None:
                self.lock.push(*self.highlighted)

    def toggle_current_pick(self):
        if self.mouse_pressed[2] and not self.mouse_was_pressed[2]:
            self.lock.change_current_pick()

    def check_win(self) -> bool:
        if self.lock.check_win():
            self.win = True
            self.running = False
            return True
        return False
