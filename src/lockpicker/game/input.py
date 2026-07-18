from __future__ import annotations

from enum import IntEnum
from typing import Final, NamedTuple, Tuple

import pygame

from lockpicker.constants.config import settings


class MouseButton(IntEnum):
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3


class Key(IntEnum):
    ESCAPE = pygame.K_ESCAPE
    UNDO = pygame.K_z
    REDO = pygame.K_y
    RESTART = pygame.K_r
    SAVE = pygame.K_s
    PLAY = pygame.K_p
    BINDING = pygame.K_b
    MASTER = pygame.K_m
    ADD = pygame.K_INSERT
    DELETE = pygame.K_DELETE


FIRST_GROUP_KEY: Final[int] = pygame.K_1
NUMBER_OF_GROUPS: Final = len(settings.color.tumblers)
GROUP_KEYS: Final[Tuple[int, ...]] = tuple(FIRST_GROUP_KEY + offset for offset in range(NUMBER_OF_GROUPS))


def group_from_key(key: int) -> int:
    return key - FIRST_GROUP_KEY


class ButtonState(NamedTuple):
    left: bool
    middle: bool
    right: bool


class MouseState:
    def __init__(self) -> None:
        self.offset: Tuple[int, int] = (0, 0)
        self.position: Tuple[int, int] = (0, 0)
        self.pressed = ButtonState(False, False, False)
        self.previous = ButtonState(False, False, False)

    def update(self) -> None:
        x, y = pygame.mouse.get_pos()
        self.position = (x - self.offset[0], y - self.offset[1])
        pressed = pygame.mouse.get_pressed()
        self.pressed = ButtonState(bool(pressed[0]), bool(pressed[1]), bool(pressed[2]))

    def commit(self) -> None:
        self.previous = self.pressed

    @property
    def left_clicked(self) -> bool:
        return self.pressed.left and not self.previous.left

    @property
    def right_clicked(self) -> bool:
        return self.pressed.right and not self.previous.right
