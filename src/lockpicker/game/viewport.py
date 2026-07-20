from __future__ import annotations

from typing import Tuple

import pygame

from lockpicker.constants.config import settings


class Viewport:
    def __init__(self, window: pygame.surface.Surface) -> None:
        self.window = window
        width, height = window.get_size()
        self.ui_scale = min(width / settings.screen.width, height / settings.screen.height)
        board_width = round(settings.screen.width * self.ui_scale)
        board_height = round(settings.screen.height * self.ui_scale)
        left = (width - board_width) // 2
        top = (height - board_height) // 2
        window.fill(settings.color.border)
        self.rect = pygame.Rect(left, top, board_width, board_height)
        self.board = window.subsurface(self.rect)

    @property
    def offset(self) -> Tuple[int, int]:
        return self.rect.topleft  # type: ignore[no-any-return]
