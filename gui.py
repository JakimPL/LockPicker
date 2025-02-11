import pygame

from constants.gui import HEIGHT, BAR_WIDTH, BAR_OFFSET, X_OFFSET, SCALE, WIDTH
from constants.gui import PICK_OFFSET, PICK_SIZE, PICK_WIDTH, PICK_IDLE_OFFSET, PICK_DISCREPANCY
from constants.gui import PICK_COLORS, TUMBLERS_COLORS
from lock import Lock
from tumbler import Tumbler


def draw_tumbler(tumbler: Tumbler, position: int, screen, mouse_pos) -> bool:
    alpha = 255 if tumbler.master else 160
    alpha /= 3 if tumbler.jammed else 1
    color = TUMBLERS_COLORS[tumbler.group]

    height = tumbler.current_height
    x = position * (BAR_WIDTH + BAR_OFFSET) + X_OFFSET
    h = height * SCALE
    if tumbler.upper:
        y = 0
    else:
        y = HEIGHT - h

    rect = pygame.Rect(x, y, BAR_WIDTH, h)

    collision = rect.collidepoint(mouse_pos)
    if collision:
        color = (0xFF, 0xFF, 0xFF)

    surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    surface.fill((*color, alpha))
    screen.blit(surface, rect.topleft)

    return collision


def draw_pick(lock: Lock, pick: int, screen):
    index = lock.picks[pick]
    alpha = 255 if pick == lock.current_pick else 160
    if index is None:
        x = PICK_IDLE_OFFSET
        y = HEIGHT // 2 + PICK_DISCREPANCY * (pick - lock.number_of_picks / 2 + 0.5)
    else:
        position, upper = index
        tumbler = lock.positions[position][upper]
        x = position * (BAR_WIDTH + BAR_OFFSET) + X_OFFSET + BAR_WIDTH // 2
        height = tumbler.current_height * SCALE
        if upper:
            y = height + PICK_OFFSET
        else:
            y = HEIGHT - height - PICK_OFFSET

    color = (*PICK_COLORS[pick], alpha)
    shape_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    if pick == 0:
        points = [(x, y - PICK_SIZE), (x - PICK_SIZE, y), (x, y + PICK_SIZE), (x + PICK_SIZE, y)]
        pygame.draw.polygon(shape_surface, color, points)
    else:
        pygame.draw.circle(shape_surface, color, (x, y), PICK_SIZE)

    rect = pygame.Rect(0, y - PICK_WIDTH // 2, x, PICK_WIDTH)
    pygame.draw.rect(shape_surface, color, rect)
    screen.blit(shape_surface, (0, 0))
