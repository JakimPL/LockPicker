from collections import deque
from typing import Deque, Optional

import pygame
from lockpicker.agents.random import RandomAgent
from lockpicker.constants.config import RendererMode
from lockpicker.engine.lock import Lock
from lockpicker.game.animation import Animation, compute_animation_steps
from lockpicker.game.input import Key, MouseState
from lockpicker.game.layout import Layout
from lockpicker.game.loop import run_loop
from lockpicker.game.render.factory import create_renderer
from lockpicker.game.render.protocol import BoardRenderer
from lockpicker.game.viewport import Viewport
from lockpicker.state.state import State
from lockpicker.tumbler.location import Location


class Game:
    def __init__(
        self,
        screen: pygame.surface.Surface,
        lock: Lock,
        *,
        random_moves: bool = False,
        renderer_mode: Optional[RendererMode] = None,
    ) -> None:
        self.screen = screen
        self.lock = lock
        self.running = False
        self.random_moves = random_moves
        self.random_agent = RandomAgent(lock)
        self.renderer_mode = renderer_mode

        self.viewport = Viewport(screen)
        self.mouse = MouseState()
        self.mouse.offset = self.viewport.offset
        self.animation = Animation()
        self.layout = Layout(lock.level.max_height, self.viewport.ui_scale)
        self.renderer: BoardRenderer = create_renderer(
            self.viewport.board, lock, self.layout, self.animation, mode=renderer_mode
        )
        self.highlighted: Optional[Location] = None

        self.undo_history: Deque[State] = deque()
        self.redo_history: Deque[State] = deque()
        self.save_state()

    def run(self) -> None:
        run_loop(self)

    def frame(self) -> None:
        self.gather_events()
        self.mouse.update()
        self.draw()
        self.action()
        self.mouse.commit()
        self.check_win()

    def gather_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.WINDOWRESIZED:
                self.rebuild_viewport()
            elif event.type == pygame.KEYDOWN:
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
            self.viewport.board, self.lock, self.layout, self.animation, mode=self.renderer_mode
        )

    def handle_key(self, key: int) -> None:
        if key == Key.ESCAPE:
            self.running = False
            return

        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            match key:
                case Key.UNDO:
                    self.undo()
                case Key.REDO:
                    self.redo()
                case Key.RESTART:
                    self.restart()

    def draw(self) -> None:
        self.renderer.draw_background()
        self.draw_tumblers()
        self.renderer.draw_picks()
        pygame.display.flip()

    def draw_tumblers(self) -> None:
        self.highlighted = None
        for location, tumbler in self.lock.get_tumblers_by_location().items():
            bounds = self.renderer.get_tumbler_bounds(tumbler)
            highlighted = self.renderer.is_mouse_hovering_tumbler(tumbler, self.mouse.position, bounds)
            self.renderer.draw_tumbler(tumbler, bounds, highlighted=highlighted)
            if highlighted:
                self.highlighted = location

    def action(self) -> None:
        self.toggle_current_pick()
        if not self.animation.advance():
            self.handle_selected_tumbler()
            if self.random_moves:
                self.random_agent.play_move()

            self.animation.load(compute_animation_steps(self.lock.drain_snapshots()))

    def handle_selected_tumbler(self) -> None:
        if self.mouse.left_clicked:
            if self.highlighted is not None:
                self.lock.push(self.highlighted)
            else:
                self.lock.release_current_pick()

            self.save_state()

    def toggle_current_pick(self) -> None:
        if self.mouse.right_clicked:
            self.lock.change_current_pick()

    def check_win(self) -> bool:
        if self.lock.check_win():
            self.running = False
            return True

        return False

    def restart(self) -> None:
        self.lock.reset()
        self.animation.reset()

    def save_state(self) -> None:
        last_state = self.undo_history[-1] if self.undo_history else None
        state = self.lock.get_state()
        if last_state != state:
            self.undo_history.append(state)
            self.redo_history.clear()

    def undo(self) -> None:
        if self.undo_history:
            self.animation.reset()
            self.redo_history.append(self.lock.get_state())
            state = self.undo_history.pop()
            self.lock.load_state(state)

    def redo(self) -> None:
        if self.redo_history:
            self.animation.reset()
            self.undo_history.append(self.lock.get_state())
            state = self.redo_history.pop()
            self.lock.load_state(state)
