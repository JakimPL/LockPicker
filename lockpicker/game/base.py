import pygame

from lockpicker.constants.gui import (
    BACKGROUND_COLOR,
    BAR_OFFSET,
    BAR_WIDTH,
    HEIGHT,
    HIGHLIGHT_COLOR,
    PICK_COLORS,
    PICK_DISCREPANCY,
    PICK_IDLE_OFFSET,
    PICK_OFFSET,
    PICK_SIZE,
    PICK_WIDTH,
    SCALE,
    TUMBLERS_COLORS,
    WIDTH,
    X_OFFSET,
)
from lockpicker.lock import Lock
from lockpicker.tumbler import Tumbler


class BaseGame:
    def __init__(self, lock: Lock):
        self.lock = lock
        self.running = False
        self.screen = self.init_pygame()
        self.mouse_pos = None
        self.mouse_pressed = (False, False, False)
        self.mouse_was_pressed = (False, False, False)
        self.highlighted = None
        self.animation = 0.0
        self.animation_items = {}

    def run(self):
        self.running = True
        while self.running:
            self.frame()
        self.terminate()

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
                self.running = False

    def get_mouse_state(self):
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_pressed = pygame.mouse.get_pressed()

    def set_mouse_state(self):
        self.mouse_was_pressed = self.mouse_pressed

    def draw_background(self):
        self.screen.fill(BACKGROUND_COLOR)

    def draw_tumblers(self):
        self.highlighted = None
        for position, items in self.lock.positions.items():
            for upper, item in items.items():
                if item is not None:
                    highlighted = self.draw_tumbler(item, position)
                    if highlighted:
                        self.highlighted = position, upper

    def draw_tumbler(self, tumbler: Tumbler, position: int) -> bool:
        alpha = 255 if tumbler.master else 160
        alpha /= 3 if tumbler.jammed else 1
        color = TUMBLERS_COLORS[tumbler.group]

        height = self.get_current_height(tumbler)
        x = position * (BAR_WIDTH + BAR_OFFSET) + X_OFFSET
        if tumbler.upper:
            h = height * SCALE
            y = 0
        else:
            h = height * SCALE
            y = HEIGHT - h

        rect = pygame.Rect(x, y, BAR_WIDTH, h)

        collision = rect.collidepoint(self.mouse_pos)
        if collision:
            color = HIGHLIGHT_COLOR

        surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surface.fill((*color, alpha))
        self.screen.blit(surface, rect.topleft)

        return collision

    def draw_picks(self):
        for pick in self.lock.picks:
            self.draw_pick(pick)

    def draw_pick(self, pick: int):
        index = self.lock.picks[pick]
        alpha = 255 if pick == self.lock.current_pick else 160
        if index is None:
            x = PICK_IDLE_OFFSET
            y = HEIGHT // 2 + PICK_DISCREPANCY * (pick - self.lock.number_of_picks / 2 + 0.5)
        else:
            position, upper = index
            tumbler = self.lock.positions[position][upper]
            height = self.get_current_height(tumbler)

            h = height * SCALE
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

    @staticmethod
    def terminate():
        pygame.quit()
