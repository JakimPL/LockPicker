from __future__ import annotations

import gzip
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Union, cast

import msgpack

from lockpicker.level.validation import BindingSpec, LevelSpec, TumblerSpec
from lockpicker.tumbler.definition import TumblerDefinition
from lockpicker.tumbler.location import Location
from lockpicker.tumbler.tumbler import Tumbler


@dataclass
class Level:
    number_of_picks: int
    max_height: int
    tumblers: Dict[Location, Tumbler]
    bindings: Dict[Location, Dict[Location, int]]

    def __post_init__(self) -> None:
        self._assign_counters()

    def validate(self) -> None:
        self.to_spec()

    @staticmethod
    def create(number_of_picks: int, max_height: int) -> Level:
        return Level(number_of_picks, max_height, {}, {})

    def copy(self) -> Level:
        tumblers = {location: tumbler.copy() for location, tumbler in self.tumblers.items()}
        bindings = {location: bindings.copy() for location, bindings in self.bindings.items()}
        return Level(
            self.number_of_picks,
            self.max_height,
            tumblers,
            bindings,
        )

    def add_binding(
        self,
        initial_location: Location,
        target_location: Location,
        difference: int,
    ) -> None:
        if difference != 0:
            if initial_location not in self.bindings:
                self.bindings[initial_location] = {target_location: difference}
            else:
                self.bindings[initial_location][target_location] = difference

    def add_tumbler(self, tumbler: Tumbler) -> None:
        self.tumblers[tumbler.location] = tumbler

    def remove_bindings(self, location: Location) -> None:
        bindings: Dict[Location, Dict[Location, int]] = {}
        for source_location, binding in self.bindings.items():
            if source_location == location:
                continue

            bindings[source_location] = {
                target_location: difference
                for target_location, difference in binding.items()
                if target_location != location
            }

        self.bindings = bindings

    def remove_tumbler(self, tumbler: Tumbler) -> None:
        location = tumbler.location
        self.remove_bindings(location)
        self.tumblers.pop(location)

    def to_spec(self) -> LevelSpec:
        return LevelSpec(
            number_of_picks=self.number_of_picks,
            max_height=self.max_height,
            tumblers=[
                TumblerSpec(
                    position=tumbler.position,
                    upper=tumbler.upper,
                    group=tumbler.group,
                    height=tumbler.base_height,
                    post_release_height=tumbler.post_release_height,
                    master=tumbler.master,
                )
                for tumbler in self.tumblers.values()
            ],
            bindings=[
                BindingSpec(
                    initial_position=initial.position,
                    initial_upper=initial.upper,
                    target_position=target.position,
                    target_upper=target.upper,
                    difference=difference,
                )
                for initial, targets in self.bindings.items()
                for target, difference in targets.items()
            ],
        )

    @classmethod
    def from_spec(cls, spec: LevelSpec) -> Level:
        tumblers: Dict[Location, Tumbler] = {}
        for tumbler_spec in spec.tumblers:
            location = Location(tumbler_spec.position, tumbler_spec.upper)
            definition = TumblerDefinition(
                location,
                tumbler_spec.group,
                tumbler_spec.height,
                tumbler_spec.post_release_height,
                tumbler_spec.master,
            )
            tumblers[location] = Tumbler(definition, spec.max_height)

        bindings: Dict[Location, Dict[Location, int]] = {}
        for binding in spec.bindings:
            initial = Location(binding.initial_position, binding.initial_upper)
            target = Location(binding.target_position, binding.target_upper)
            bindings.setdefault(initial, {})[target] = binding.difference

        return cls(spec.number_of_picks, spec.max_height, tumblers, bindings)

    def serialize(self) -> bytes:
        return cast(bytes, msgpack.packb(self.to_spec().model_dump()))

    @classmethod
    def deserialize(cls, data: bytes) -> Level:
        spec = LevelSpec.model_validate(msgpack.unpackb(data, raw=False))
        return cls.from_spec(spec)

    def save(self, filepath: Union[str, os.PathLike[str]]) -> None:
        with gzip.open(filepath, "wb") as file:
            file.write(self.serialize())

    @staticmethod
    def load(filepath: Union[str, os.PathLike[str]]) -> Level:
        with gzip.open(filepath, "rb") as file:
            return Level.deserialize(file.read())

    def _assign_counters(self) -> None:
        for location, tumbler in self.tumblers.items():
            tumbler.set_counter(self.tumblers.get(location.counter))

    @property
    def groups(self) -> DefaultDict[int, List[Location]]:
        groups: DefaultDict[int, List[Location]] = defaultdict(list)
        for location, tumbler in self.tumblers.items():
            groups[tumbler.group].append(location)

        return groups

    def get_group(self, group: int) -> List[Location]:
        return self.groups[group]

    def set_master(self, location: Location) -> None:
        tumbler = self.tumblers[location]
        for other in self.get_group(tumbler.group):
            self.tumblers[other].set_master(False)

        tumbler.set_master(True)
