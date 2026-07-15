import os
from pathlib import Path
from typing import Callable, Union

import pygame

from lockpicker.engine.lock import Lock
from lockpicker.game.animation import Animation
from lockpicker.game.editor.geometry import EditorGeometry
from lockpicker.game.editor.input import EditorInput
from lockpicker.game.editor.rendering import EditorRenderer
from lockpicker.game.editor.snapshot import EditorSnapshots
from lockpicker.game.editor.state import EditorState
from lockpicker.game.input import Key, MouseState
from lockpicker.game.layout import Layout
from lockpicker.game.loop import run_loop
from lockpicker.game.renderer import Renderer


class Editor:
    def __init__(
        self,
        screen: pygame.surface.Surface,
        lock: Lock,
        path: Union[str, os.PathLike[str]],
        run_game_callback: Callable[[], None],
    ) -> None:
        self.screen = screen
        self.lock = lock
        self.running = False

        self.mouse = MouseState()
        self.animation = Animation()
        self.layout = Layout(lock.level.max_height)
        self.renderer = Renderer(screen, lock, self.layout, self.animation)

        self.state = EditorState()
        self.geometry = EditorGeometry(lock, self.layout, self.mouse)
        self.snapshots = EditorSnapshots(lock, self.state)
        self.input = EditorInput(
            lock,
            Path(path),
            self.state,
            self.geometry,
            self.snapshots,
            run_game_callback,
        )
        self.rendering = EditorRenderer(
            self.renderer,
            lock,
            self.state,
            self.geometry,
            self.mouse,
        )

    def run(self) -> None:
        run_loop(self)

    def frame(self) -> None:
        self.gather_events()
        self.mouse.update()
        self.rendering.draw()
        self.input.handle_dragging(self.mouse.pressed)
        self.mouse.commit()

    def gather_events(self) -> None:
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    self.running = False
                case pygame.MOUSEBUTTONDOWN:
                    self.input.handle_mouse_button(event.button)
                case pygame.KEYDOWN:
                    self.handle_key(event.key)

    def handle_key(self, key: int) -> None:
        if key == Key.ESCAPE:
            self.running = False
            return

        self.input.handle_key(key)
