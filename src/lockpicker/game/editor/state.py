from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from lockpicker.tumbler.location import Location


@dataclass
class EditorState:
    highlighted: Optional[Location] = None
    dragging_tumbler: Optional[Location] = None
    initial_height: Optional[int] = None
    binding_initial: Optional[Location] = None
    binding_target: Optional[Location] = None
    current_group: int = 0

    def reset_selections(self) -> None:
        self.highlighted = None
        self.binding_initial = None
        self.binding_target = None
        self.dragging_tumbler = None
        self.initial_height = None
