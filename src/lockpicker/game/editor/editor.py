import os
from pathlib import Path
from typing import Callable, Optional, Union

import pygame

from lockpicker.constants.config import RendererMode
from lockpicker.engine.lock import Lock
from lockpicker.game.animation import Animation
from lockpicker.game.editor.geometry import EditorGeometry
from lockpicker.game.editor.input import EditorInput
from lockpicker.game.editor.rendering import EditorRenderer
from lockpicker.game.editor.snapshot import EditorSnapshots
from lockpicker.game.editor.state import EditorState
from lockpicker.game.effects import LipEffects
from lockpicker.game.input import Key, MouseState
from lockpicker.game.layout import Layout
from lockpicker.game.loop import run_loop
from lockpicker.game.render.factory import create_renderer
from lockpicker.game.render.protocol import BoardRenderer
from lockpicker.game.viewport import Viewport


class Editor:
    def __init__(
        self,
        screen: pygame.surface.Surface,
        lock: Lock,
        path: Union[str, os.PathLike[str]],
        run_game_callback: Callable[[], None],
        *,
        renderer_mode: Optional[RendererMode] = None,
    ) -> None:
        self.screen = screen
        self.lock = lock
        self.running = False
        self.renderer_mode = renderer_mode

        self.viewport = Viewport(screen)
        self.mouse = MouseState()
        self.mouse.offset = self.viewport.offset
        self.animation = Animation()
        self.effects = LipEffects()
        self.layout = Layout(lock.level.max_height, self.viewport.ui_scale)
        self.renderer: BoardRenderer = create_renderer(
            self.viewport.board, lock, self.layout, self.animation, self.effects, mode=renderer_mode
        )

        self.run_game_callback = run_game_callback
        self.state = EditorState()
        self.geometry = EditorGeometry(lock, self.layout, self.mouse)
        self.snapshots = EditorSnapshots(lock, self.state)
        self.input = EditorInput(
            lock,
            Path(path),
            self.state,
            self.geometry,
            self.snapshots,
            self.run_game,
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

    def run_game(self) -> None:
        self.run_game_callback()
        self.rebuild_viewport()

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
                case pygame.WINDOWRESIZED:
                    self.rebuild_viewport()
                case pygame.MOUSEBUTTONDOWN:
                    self.input.handle_mouse_button(event.button)
                case pygame.KEYDOWN:
                    self.handle_key(event.key)

    def rebuild_viewport(self) -> None:
        window = pygame.display.get_surface()
        if window is None:
            return

        self.screen = window
        self.viewport = Viewport(window)
        self.layout.rescale(self.viewport.ui_scale)
        self.mouse.offset = self.viewport.offset
        self.renderer = create_renderer(
            self.viewport.board, self.lock, self.layout, self.animation, self.effects, mode=self.renderer_mode
        )
        self.rendering.renderer = self.renderer

    def handle_key(self, key: int) -> None:
        if key == Key.ESCAPE:
            self.running = False
            return

        self.input.handle_key(key)
