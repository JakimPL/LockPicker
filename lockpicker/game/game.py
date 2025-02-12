import pygame

from lockpicker.constants.gui import ANIMATION_SPEED
from lockpicker.game.base import BaseGame
from lockpicker.lock import Lock


class Game(BaseGame):
    def __init__(self, screen: pygame.surface.Surface, lock: Lock):
        super().__init__(screen, lock)
        self.win = False
        self.loss = False

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
            self.lock.current_pick = 1 - self.lock.current_pick

    def check_win(self) -> bool:
        if self.lock.check_win():
            self.win = True
            self.running = False
            return True
        return False
