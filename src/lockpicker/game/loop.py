from __future__ import annotations

from typing import Protocol

import pygame

from lockpicker.constants.config import settings


class Frame(Protocol):
    running: bool

    def frame(self) -> None: ...


def run_loop(frame: Frame) -> None:
    clock = pygame.time.Clock()
    frame.running = True
    while frame.running:
        frame.frame()
        clock.tick(settings.animation.fps)
