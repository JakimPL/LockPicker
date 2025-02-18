import gzip
import os
import struct
import warnings
from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Optional, Tuple, Union

from lockpicker.location import Location
from lockpicker.tumblers.tumbler import Tumbler

MAX_HEIGHT = 11
NUMBER_OF_PICKS = 2


@dataclass
class Level:
    number_of_picks: int
    max_height: int
    tumblers: Dict[Location, Tumbler]
    bindings: Dict[Location, Dict[Location, int]]
    groups: Optional[DefaultDict[int, List[Location]]] = None

    def __post_init__(self):
        self._assign_counters()
        self.groups = self._create_groups()

    def validate(self):
        assert all(tumbler.position >= 0 for tumbler in self.tumblers)
        assert all(0 < tumbler.base_height < self.max_height for tumbler in self.tumblers.values())

        tumblers = {(tumbler.group, tumbler.location) for tumbler in self.tumblers.values()}
        assert len(tumblers) == len(self.tumblers)

        assert self._create_groups() == self.groups

        master_groups = defaultdict(list)
        for tumbler in self.tumblers.values():
            master_groups[tumbler.group].append(tumbler.master)

        for group, tumblers in master_groups.items():
            if sum(tumblers) != 1:
                warnings.warn(f"Group {group} doesn't have a master tumbler")

    @staticmethod
    def create(number_of_picks: int = NUMBER_OF_PICKS, max_height: int = MAX_HEIGHT) -> "Level":
        return Level(number_of_picks, max_height, {}, {})

    def copy(self) -> "Level":
        tumblers = {location: tumbler.copy() for location, tumbler in self.tumblers.items()}
        bindings = {location: bindings.copy() for location, bindings in self.bindings.items()}
        return Level(
            self.number_of_picks,
            self.max_height,
            tumblers,
            bindings,
        )

    def add_binding(self, initial_location: Location, target_location: Location, difference: int):
        if difference != 0:
            if initial_location not in self.bindings:
                self.bindings[initial_location] = {target_location: difference}
            else:
                self.bindings[initial_location][target_location] = difference

    def add_tumbler(self, tumbler: Tumbler):
        self.tumblers[tumbler.location] = tumbler
        self.groups[tumbler.group].append(tumbler.location)

    def remove_bindings(self, location: Location):
        bindings = {}
        for loc, binding in self.bindings.items():
            if loc == location:
                continue

            bindings[loc] = {l: d for l, d in binding.items() if l != location}

        self.bindings = bindings

    def remove_tumbler(self, tumbler: Tumbler):
        location = tumbler.location
        self.remove_bindings(location)
        self.tumblers.pop(location)
        self.groups[tumbler.group].remove(location)
        del tumbler

    def serialize_tumblers(self) -> bytes:
        tumblers_count = struct.pack("I", len(self.tumblers))
        tumblers_data = b"".join(tumbler.serialize() for tumbler in self.tumblers.values())
        return tumblers_count + tumblers_data

    def serialize_bindings(self) -> bytes:
        bindings_data = struct.pack("I", len(self.bindings))
        for position, bindings in self.bindings.items():
            bindings_data += struct.pack("I?", *position)
            bindings_data += struct.pack("I", len(bindings))
            for (p, u), d in bindings.items():
                bindings_data += struct.pack("I?i", p, u, d)

        return bindings_data

    def serialize(self) -> Tuple[bytes, ...]:
        number_of_picks = struct.pack("I", self.number_of_picks)
        max_height = struct.pack("I", self.max_height)
        serialized_tumblers = self.serialize_tumblers()
        serialized_bindings = self.serialize_bindings()
        return number_of_picks, max_height, serialized_tumblers, serialized_bindings

    def save(self, filepath: Union[str, os.PathLike]):
        with gzip.open(filepath, "wb") as file:
            number_of_picks, max_height, serialized_tumblers, serialized_bindings = self.serialize()
            tumblers_block_size = struct.pack("I", len(serialized_tumblers))
            bindings_block_size = struct.pack("I", len(serialized_tumblers))
            file.write(number_of_picks)
            file.write(max_height)
            file.write(tumblers_block_size)
            file.write(serialized_tumblers)
            file.write(bindings_block_size)
            file.write(serialized_bindings)
            print(f"Level saved to {filepath}.")

    @staticmethod
    def deserialize_tumblers(data: bytes, max_height: int) -> Dict[Location, Tumbler]:
        tumblers_count = struct.unpack("I", data[:4])[0]
        tumblers = {}
        size = struct.calcsize(Tumbler.struct_format)
        for i in range(tumblers_count):
            tumbler_data = data[4 + i * size : 4 + (i + 1) * size]
            tumbler = Tumbler.deserialize(tumbler_data, max_height)
            tumblers[tumbler.location] = tumbler

        return tumblers

    @staticmethod
    def deserialize_bindings(data: bytes) -> Dict[Location, Dict[Location, int]]:
        bindings_count = struct.unpack("I", data[:4])[0]
        bindings = {}
        offset = 4
        for i in range(bindings_count):
            location = struct.unpack("I?", data[offset : offset + 5])
            offset += 5
            binding_count = struct.unpack("I", data[offset : offset + 4])[0]
            offset += 4
            binding = {}
            for _ in range(binding_count):
                p, u, d = struct.unpack("I?i", data[offset : offset + 12])
                offset += 12
                binding[Location(p, u)] = d
            bindings[Location(*location)] = binding

        return bindings

    def deserialize(self, data: Tuple[bytes, ...]) -> "Level":
        number_of_picks_data, max_height_data, tumblers_data, bindings_data = data
        number_of_picks = struct.unpack("I", number_of_picks_data)[0]
        max_height = struct.unpack("I", max_height_data)[0]
        tumblers = Level.deserialize_tumblers(tumblers_data, self.max_height)
        bindings = Level.deserialize_bindings(bindings_data)
        return Level(number_of_picks, max_height, tumblers, bindings)

    @staticmethod
    def load(filepath: Union[str, os.PathLike]) -> "Level":
        with gzip.open(filepath, "rb") as file:
            number_of_picks_data = file.read(4)
            max_height_data = file.read(4)
            tumblers_block_size = struct.unpack("I", file.read(4))[0]
            tumblers_data = file.read(tumblers_block_size)
            bindings_block_size = struct.unpack("I", file.read(4))[0]
            bindings_data = file.read(bindings_block_size)

            number_of_picks = struct.unpack("I", number_of_picks_data)[0]
            max_height = struct.unpack("I", max_height_data)[0]
            tumblers = Level.deserialize_tumblers(tumblers_data, max_height)
            bindings = Level.deserialize_bindings(bindings_data)
            return Level(number_of_picks, max_height, tumblers, bindings)

    def _assign_counters(self):
        for location, tumbler in self.tumblers.items():
            tumbler.counter = self.tumblers.get(location.counter)

    def _create_groups(self) -> DefaultDict[int, List[Location]]:
        groups = defaultdict(list)
        for location, tumbler in self.tumblers.items():
            groups[tumbler.group].append(location)

        return groups
