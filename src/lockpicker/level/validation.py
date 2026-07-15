from __future__ import annotations

import warnings
from typing import Dict, List, Set, Tuple

from pydantic import BaseModel, Field, model_validator


class TumblerSpec(BaseModel):
    position: int = Field(ge=0)
    upper: bool
    group: int = Field(ge=0)
    height: int = Field(gt=0)
    post_release_height: int = 0
    master: bool = False


class BindingSpec(BaseModel):
    initial_position: int = Field(ge=0)
    initial_upper: bool
    target_position: int = Field(ge=0)
    target_upper: bool
    difference: int


class LevelSpec(BaseModel):
    number_of_picks: int = Field(ge=1)
    max_height: int = Field(ge=1)
    tumblers: List[TumblerSpec]
    bindings: List[BindingSpec] = []

    @model_validator(mode="after")
    def _validate_tumblers(self) -> LevelSpec:
        seen: Set[Tuple[int, int, bool]] = set()
        masters: Dict[int, int] = {}
        for tumbler in self.tumblers:
            if tumbler.height > self.max_height:
                raise ValueError(f"Tumbler height must be within (0, {self.max_height}], got {tumbler.height}")

            key = (tumbler.group, tumbler.position, tumbler.upper)
            if key in seen:
                raise ValueError(
                    f"Duplicate tumbler in group {tumbler.group} at position ({tumbler.position}, {tumbler.upper})"
                )

            seen.add(key)
            masters[tumbler.group] = masters.get(tumbler.group, 0) + int(tumbler.master)

        for group, count in masters.items():
            if count != 1:
                warnings.warn(f"Group {group} doesn't have a master tumbler")

        return self
