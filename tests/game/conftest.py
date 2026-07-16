from __future__ import annotations

from typing import Iterator

import pygame
import pytest
from lockpicker.constants.config import RendererMode, settings
from lockpicker.engine.lock import Lock
from lockpicker.level.level import Level
from lockpicker.paths import LEVELS_DIR

LEVEL_PATH = LEVELS_DIR / "level_01_01.lvl"


@pytest.fixture
def screen() -> Iterator[pygame.surface.Surface]:
    pygame.display.init()
    surface = pygame.display.set_mode((settings.screen.width, settings.screen.height))
    yield surface
    pygame.display.quit()


@pytest.fixture(params=list(RendererMode), ids=[mode.value for mode in RendererMode])
def renderer_mode(request: pytest.FixtureRequest) -> RendererMode:
    mode: RendererMode = request.param
    return mode


@pytest.fixture
def sample_lock() -> Lock:
    return Lock(Level.load(LEVEL_PATH))
