from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pygame
import pytest

from lockpicker.constants.config import settings
from lockpicker.engine.lock import Lock
from lockpicker.game.editor.editor import Editor
from lockpicker.game.game import Game


def grid_point(position: int, *, upper: bool) -> Tuple[int, int]:
    x = position * (settings.layout.bar_width + settings.layout.bar_offset) + settings.layout.x_offset
    x += settings.layout.bar_width // 2
    y = settings.screen.height // 4 if upper else settings.screen.height * 3 // 4
    return x, y


def pump(target: object, frames: int = 3) -> None:
    target.running = True
    for _ in range(frames):
        target.frame()


def assert_level_within_bounds(lock: Lock) -> None:
    for tumbler in lock.level.tumblers.values():
        assert 1 <= tumbler.height <= lock.level.max_height


def test_game_frame_renders_and_quit_stops(screen: pygame.surface.Surface, sample_lock: Lock) -> None:
    game = Game(screen, sample_lock, random_moves=False)
    pump(game)
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    game.frame()
    assert game.running is False


def test_game_handles_click_and_undo(
    screen: pygame.surface.Surface,
    sample_lock: Lock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = Game(screen, sample_lock, random_moves=False)
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: grid_point(0, upper=False))
    presses = iter([(True, False, False), (False, False, False), (False, False, True)])
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda *args, **kwargs: next(presses, (False, False, False)))
    pump(game, frames=3)

    monkeypatch.setattr(pygame.key, "get_mods", lambda: pygame.KMOD_CTRL)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z))
    game.frame()
    assert game.running is True
    assert_level_within_bounds(game.lock)


def test_editor_frame_renders_and_quit_stops(
    screen: pygame.surface.Surface,
    sample_lock: Lock,
    tmp_path: Path,
) -> None:
    editor = Editor(screen, sample_lock, tmp_path / "out.lvl", lambda: None)
    pump(editor)
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    editor.frame()
    assert editor.running is False


def test_editor_event_dispatch(
    screen: pygame.surface.Surface,
    sample_lock: Lock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    editor = Editor(screen, sample_lock, tmp_path / "out.lvl", lambda: None)
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: grid_point(3, upper=True))
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda *args, **kwargs: (False, False, False))
    editor.running = True
    editor.frame()

    events = [
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_INSERT),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b),
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DELETE),
    ]
    for event in events:
        pygame.event.post(event)
        editor.frame()

    monkeypatch.setattr(pygame.key, "get_mods", lambda: pygame.KMOD_CTRL)
    for key in (pygame.K_z, pygame.K_y):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
        editor.frame()

    assert editor.running is True
    assert_level_within_bounds(editor.lock)
