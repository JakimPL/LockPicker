from __future__ import annotations

from pathlib import Path
from typing import Callable

import pygame

from lockpicker.engine.lock import Lock
from lockpicker.game.editor.geometry import EditorGeometry
from lockpicker.game.editor.snapshot import EditorSnapshots
from lockpicker.game.editor.state import EditorState
from lockpicker.game.input import GROUP_KEYS, ButtonState, Key, MouseButton, group_from_key


class EditorInput:
    def __init__(
        self,
        lock: Lock,
        path: Path,
        state: EditorState,
        geometry: EditorGeometry,
        snapshots: EditorSnapshots,
        run_game_callback: Callable[[], None],
    ) -> None:
        self.lock = lock
        self.path = path
        self.state = state
        self.geometry = geometry
        self.snapshots = snapshots
        self.run_game_callback = run_game_callback

    def handle_mouse_button(self, button: int) -> None:
        match button:
            case MouseButton.LEFT:
                if self.state.binding_initial is not None:
                    self.handle_binding_key()
            case MouseButton.RIGHT:
                self.cancel_binding()

    def handle_key(self, key: int) -> None:
        match key:
            case Key.BINDING:
                self.handle_binding_key()
            case Key.MASTER:
                self.set_master_tumbler()
            case Key.ADD:
                self.add_new_tumbler()
            case Key.DELETE:
                self.delete_highlighted_tumbler()
            case _ if key in GROUP_KEYS:
                self.change_group(group_from_key(key))

        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.handle_ctrl_key(key)

    def handle_ctrl_key(self, key: int) -> None:
        match key:
            case Key.UNDO:
                self.snapshots.undo()
            case Key.REDO:
                self.snapshots.redo()
            case Key.SAVE:
                self.save_level()
            case Key.PLAY:
                self.run_game_callback()
                self.state.highlighted = None

    def add_new_tumbler(self) -> None:
        if self.state.highlighted is None:
            location = self.geometry.pointer_location()
            if location is None:
                return

            if self.lock.get_tumbler(location) is None:
                tumbler = self.geometry.temp_tumbler(location, self.state.current_group)
                self.lock.level.add_tumbler(tumbler)

            self.snapshots.save_state()

    def delete_highlighted_tumbler(self) -> None:
        if self.state.highlighted is not None:
            tumbler = self.lock.get_tumbler(self.state.highlighted)
            if tumbler is not None:
                self.lock.level.remove_tumbler(tumbler)

            self.state.highlighted = None
            self.snapshots.save_state()

    def set_master_tumbler(self) -> None:
        if self.state.highlighted is not None:
            self.lock.level.set_master(self.state.highlighted)
            self.snapshots.save_state()

    def change_group(self, group: int) -> None:
        self.state.current_group = group
        if self.state.highlighted is not None:
            tumbler = self.lock.get_tumbler(self.state.highlighted)
            if tumbler is not None:
                tumbler.set_group(group)

    def handle_binding_key(self) -> None:
        if self.state.binding_initial is None:
            self.start_binding()
        elif self.state.binding_target is None:
            self.set_binding_target()
        else:
            self.complete_binding()

    def start_binding(self) -> None:
        if self.state.highlighted is not None:
            self.state.binding_initial = self.state.highlighted

    def set_binding_target(self) -> None:
        if self.state.highlighted is not None and self.state.highlighted != self.state.binding_initial:
            self.state.binding_target = self.state.highlighted

    def complete_binding(self) -> None:
        if self.state.binding_initial is not None and self.state.binding_target is not None:
            difference = self.geometry.calculate_difference(self.state.binding_target)
            self.lock.level.add_binding(self.state.binding_initial, self.state.binding_target, difference)
            self.cancel_binding()
            self.snapshots.save_state()

    def cancel_binding(self) -> None:
        self.state.binding_initial = None
        self.state.binding_target = None
        self.state.highlighted = None

    def handle_dragging(self, pressed: ButtonState) -> None:
        if self.state.binding_initial is not None:
            return

        if pressed.left:
            self.drag_height()
        elif pressed.right:
            self.drag_post_release_height()
        else:
            self.end_dragging()

    def drag_height(self) -> None:
        if self.state.dragging_tumbler is None and self.state.highlighted is not None:
            self.state.dragging_tumbler = self.state.highlighted

        if self.state.dragging_tumbler is not None:
            tumbler = self.lock.get_tumbler(self.state.dragging_tumbler)
            if tumbler is not None:
                new_height = self.geometry.calculate_new_height(self.state.dragging_tumbler)
                tumbler.set_height(new_height)

    def drag_post_release_height(self) -> None:
        if self.state.dragging_tumbler is None and self.state.highlighted is not None:
            self.state.dragging_tumbler = self.state.highlighted
            tumbler = self.lock.get_tumbler(self.state.dragging_tumbler)
            if tumbler is not None:
                self.state.initial_height = tumbler.height

        if self.state.dragging_tumbler is not None:
            tumbler = self.lock.get_tumbler(self.state.dragging_tumbler)
            if tumbler is not None and self.state.initial_height is not None:
                new_height = self.geometry.calculate_new_height(self.state.dragging_tumbler, limit=False)
                tumbler.set_post_release_height(new_height - self.state.initial_height)

    def end_dragging(self) -> None:
        if self.state.dragging_tumbler is not None:
            self.snapshots.save_state()

        self.state.dragging_tumbler = None
        self.state.initial_height = None

    def save_level(self) -> None:
        self.lock.level.save(self.path)
