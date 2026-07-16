from __future__ import annotations

from typing import Optional

import pygame
from lockpicker.constants.config import RendererMode, settings
from lockpicker.engine.lock import Lock
from lockpicker.game.animation import Animation
from lockpicker.game.assets.library import AssetLibrary
from lockpicker.game.assets.sprites import ThemeSprites
from lockpicker.game.layout import Layout
from lockpicker.game.render.flat import FlatRenderer
from lockpicker.game.render.protocol import BoardRenderer
from lockpicker.game.render.styled import StyledRenderer


def create_renderer(
    screen: pygame.surface.Surface,
    lock: Lock,
    layout: Layout,
    animation: Animation,
    *,
    mode: Optional[RendererMode] = None,
) -> BoardRenderer:
    mode = settings.theme.mode if mode is None else mode
    match mode:
        case RendererMode.STYLED:
            library = AssetLibrary.load()
            sprites = ThemeSprites(library, layout)
            return StyledRenderer(screen, lock, layout, animation, sprites)
        case _:
            return FlatRenderer(screen, lock, layout, animation)
