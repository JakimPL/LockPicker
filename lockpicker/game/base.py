from typing import Optional, Tuple

import pygame

from lockpicker.constants.gui import (
    BACKGROUND_COLOR,
    BAR_OFFSET,
    BAR_WIDTH,
    BAR_Y_OFFSET,
    HEIGHT,
    HIGHLIGHT_COLOR,
    PICK_COLORS,
    PICK_DISCREPANCY,
    PICK_IDLE_OFFSET,
    PICK_OFFSET,
    PICK_SIZE,
    PICK_WIDTH,
    TUMBLERS_COLORS,
    WIDTH,
    X_OFFSET,
)
from lockpicker.lock import Lock
from lockpicker.tumbler import Tumbler


class BaseGame:
    def __init__(self, screen: pygame.surface.Surface, lock: Lock):
        self.screen = screen
        self.running = False

        self.lock = lock

        self.mouse_pos = None
        self.mouse_pressed = (False, False, False)
        self.mouse_was_pressed = (False, False, False)

        self.highlighted = None
        self.animation = 0.0
        self.animation_items = {}
        self.scale = (HEIGHT - BAR_Y_OFFSET) / self.lock.level.max_height

    def run(self):
        self.running = True
        while self.running:
            self.frame()

    def frame(self):
        raise NotImplementedError("frame method must be implemented in child class")

    @staticmethod
    def init_pygame():
        pygame.init()
        pygame.display.set_caption("LockPicker")
        return pygame.display.set_mode((WIDTH, HEIGHT))

    def gather_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.terminate()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.terminate()
                if event.key == pygame.K_r:
                    self.lock.reset()

    def get_mouse_state(self):
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_pressed = pygame.mouse.get_pressed()

    def set_mouse_state(self):
        self.mouse_was_pressed = self.mouse_pressed

    def draw_background(self):
        self.screen.fill(BACKGROUND_COLOR)

    def draw_tumblers(self):
        self.highlighted = None
        for position, items in self.lock.get_tumblers_by_position().items():
            for upper, tumbler in items.items():
                if tumbler is not None:
                    bounds = self.get_tumbler_bounds(tumbler)
                    highlighted = self.is_mouse_hovering_tumbler(tumbler, bounds)
                    self.draw_tumbler(tumbler, bounds, highlighted)
                    if highlighted:
                        self.highlighted = position, upper

    def get_tumbler_bounds(self, tumbler: Tumbler) -> Tuple[int, int, int, int]:
        height = self.get_current_height(tumbler)
        x = tumbler.position * (BAR_WIDTH + BAR_OFFSET) + X_OFFSET
        if tumbler.upper:
            h = height * self.scale
            y = 0
        else:
            h = height * self.scale
            y = HEIGHT - h

        return x, y, BAR_WIDTH, h

    def is_mouse_hovering_tumbler(self, tumbler: Tumbler, bounds: Optional[Tuple[int, int, int, int]] = None) -> bool:
        rect = pygame.Rect(*self.get_tumbler_bounds(tumbler) if bounds is None else bounds)
        return rect.collidepoint(self.mouse_pos)

    def draw_tumbler(
        self,
        tumbler: Tumbler,
        bounds: Optional[Tuple[int, int, int, int]] = None,
        highlighted: bool = False,
        alpha: Optional[int] = None,
    ):
        if alpha is None:
            alpha = 255 if tumbler.master else 160
            alpha /= 3 if tumbler.jammed else 1

        color = HIGHLIGHT_COLOR if highlighted else TUMBLERS_COLORS[tumbler.group]
        rect = pygame.Rect(*self.get_tumbler_bounds(tumbler) if bounds is None else bounds)
        surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surface.fill((*color, alpha))
        self.screen.blit(surface, rect.topleft)

    def draw_picks(self):
        for pick in range(self.lock.level.number_of_picks):
            self.draw_pick(pick)

    def draw_pick(self, pick: int):
        index = self.lock.get_pick(pick)
        alpha = 255 if pick == self.lock.current_pick else 160
        if index is None:
            x = PICK_IDLE_OFFSET
            y = HEIGHT // 2 + PICK_DISCREPANCY * (pick - self.lock.level.number_of_picks / 2 + 0.5)
        else:
            position, upper = index
            tumbler = self.lock.get_tumbler(position, upper)
            height = self.get_current_height(tumbler)

            h = height * self.scale
            x = position * (BAR_WIDTH + BAR_OFFSET) + X_OFFSET + BAR_WIDTH // 2
            y = h + PICK_OFFSET if upper else HEIGHT - h - PICK_OFFSET

        color = (*PICK_COLORS[pick], alpha)
        shape_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        if pick == 0:
            points = [
                (x, y - PICK_SIZE),
                (x - PICK_SIZE, y),
                (x, y + PICK_SIZE),
                (x + PICK_SIZE, y),
            ]
            pygame.draw.polygon(shape_surface, color, points)
        else:
            pygame.draw.circle(shape_surface, color, (x, y), PICK_SIZE)

        rect = pygame.Rect(0, y - PICK_WIDTH // 2, x, PICK_WIDTH)
        pygame.draw.rect(shape_surface, color, rect)
        self.screen.blit(shape_surface, (0, 0))

    @staticmethod
    def get_tumbler_x(position: int) -> int:
        return position * (BAR_WIDTH + BAR_OFFSET) + X_OFFSET + BAR_WIDTH // 2

    def get_tumbler_y(self, upper: bool, height: int) -> int:
        if upper:
            return height * self.scale
        else:
            return HEIGHT - height * self.scale

    def get_current_height(self, tumbler: Tumbler) -> int:
        if (tumbler.position, tumbler.upper) in self.animation_items:
            start, end = self.animation_items[(tumbler.position, tumbler.upper)]
            if end > start:
                height = start + min(self.animation, end - start)
            else:
                height = start + max(-self.animation, end - start)
        else:
            height = tumbler.height

        return height

    def terminate(self):
        self.running = False
