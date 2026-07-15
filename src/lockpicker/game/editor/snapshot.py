from __future__ import annotations

from collections import deque
from typing import Deque, Dict, NamedTuple

from lockpicker.engine.lock import Lock
from lockpicker.game.editor.state import EditorState
from lockpicker.level.level import Level
from lockpicker.tumbler.definition import TumblerDefinition
from lockpicker.tumbler.location import Location
from lockpicker.tumbler.tumbler import Tumbler


class LevelSnapshot(NamedTuple):
    number_of_picks: int
    max_height: int
    tumblers: Dict[Location, TumblerDefinition]
    bindings: Dict[Location, Dict[Location, int]]


class EditorSnapshots:
    def __init__(self, lock: Lock, state: EditorState) -> None:
        self.lock = lock
        self.state = state
        self.undo_history: Deque[LevelSnapshot] = deque()
        self.redo_history: Deque[LevelSnapshot] = deque()
        self.save_state()

    def capture(self) -> LevelSnapshot:
        level = self.lock.level
        tumblers = {location: tumbler.definition for location, tumbler in level.tumblers.items()}
        bindings = {location: dict(targets) for location, targets in level.bindings.items()}
        return LevelSnapshot(level.number_of_picks, level.max_height, tumblers, bindings)

    def restore(self, snapshot: LevelSnapshot) -> None:
        tumblers = {
            location: Tumbler(definition, snapshot.max_height) for location, definition in snapshot.tumblers.items()
        }
        bindings = {location: dict(targets) for location, targets in snapshot.bindings.items()}
        self.lock.level = Level(snapshot.number_of_picks, snapshot.max_height, tumblers, bindings)

    def save_state(self) -> None:
        snapshot = self.capture()
        last_state = self.undo_history[-1] if self.undo_history else None
        if last_state != snapshot:
            self.undo_history.append(snapshot)
            self.redo_history.clear()

    def undo(self) -> None:
        if self.undo_history:
            self.state.reset_selections()
            self.redo_history.append(self.capture())
            snapshot = self.undo_history.pop()
            self.restore(snapshot)

    def redo(self) -> None:
        if self.redo_history:
            self.state.reset_selections()
            self.undo_history.append(self.capture())
            snapshot = self.redo_history.pop()
            self.restore(snapshot)
