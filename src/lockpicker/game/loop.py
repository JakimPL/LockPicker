from __future__ import annotations

from typing import Protocol


class Frame(Protocol):
    running: bool

    def frame(self) -> None: ...


def run_loop(frame: Frame) -> None:
    frame.running = True
    while frame.running:
        frame.frame()
