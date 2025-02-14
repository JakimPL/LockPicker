import gzip
import os
import struct
import warnings
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union

from lockpicker.tumbler import Tumbler

MAX_HEIGHT = 11
NUMBER_OF_PICKS = 2


@dataclass
class Level:
    number_of_picks: int
    max_height: int
    tumblers: List[Tumbler]
    bindings: Dict[Tuple[int, bool], Dict[Tuple[int, bool], int]]

    def validate(self):
        assert all(tumbler.position >= 0 for tumbler in self.tumblers)
        assert all(0 < tumbler.base_height < self.max_height for tumbler in self.tumblers)

        tumblers = {(tumbler.group, tumbler.upper, tumbler.position) for tumbler in self.tumblers}
        assert len(tumblers) == len(self.tumblers)

        master_groups = defaultdict(list)
        for tumbler in self.tumblers:
            master_groups[tumbler.group].append(tumbler.master)

        for group, tumblers in master_groups.items():
            if sum(tumblers) != 1:
                warnings.warn(f"Group {group} doesn't have a master tumbler")

    @staticmethod
    def create(number_of_picks: int = NUMBER_OF_PICKS, max_height: int = MAX_HEIGHT) -> "Level":
        return Level(number_of_picks, max_height, [], {})

    def copy(self) -> "Level":
        tumblers = [tumbler.copy() for tumbler in self.tumblers]
        bindings = {position: bindings.copy() for position, bindings in self.bindings.items()}
        return Level(
            self.number_of_picks,
            self.max_height,
            tumblers,
            bindings,
        )

    def add_binding(self, initial_pos: int, initial_up: bool, target_pos: int, target_up: bool, difference: int):
        if difference != 0:
            key = (initial_pos, initial_up)
            if key not in self.bindings:
                self.bindings[key] = {(target_pos, target_up): difference}
            else:
                self.bindings[key][(target_pos, target_up)] = difference

    def add_tumbler(self, tumbler: Tumbler):
        self.tumblers.append(tumbler)

    def remove_tumbler(self, tumbler: Tumbler):
        position, upper = tumbler.position, tumbler.upper
        bindings = {}
        for (pos, up), binding in self.bindings.items():
            if (pos, up) == (position, upper):
                continue

            bindings[(pos, up)] = {(p, u): d for (p, u), d in binding.items() if p != position or u != upper}

        self.bindings = bindings
        self.tumblers.remove(tumbler)
        del tumbler

    def serialize_tumblers(self) -> bytes:
        tumblers_count = struct.pack("I", len(self.tumblers))
        tumblers_data = b"".join(tumbler.serialize() for tumbler in self.tumblers)
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
    def deserialize_tumblers(data: bytes) -> List[Tumbler]:
        tumblers_count = struct.unpack("I", data[:4])[0]
        tumblers = []
        size = struct.calcsize(Tumbler.struct_format)
        for i in range(tumblers_count):
            tumbler_data = data[4 + i * size : 4 + (i + 1) * size]
            tumbler = Tumbler.deserialize(tumbler_data)
            tumblers.append(tumbler)

        return tumblers

    @staticmethod
    def deserialize_bindings(data: bytes) -> Dict[Tuple[int, bool], Dict[Tuple[int, bool], int]]:
        bindings_count = struct.unpack("I", data[:4])[0]
        bindings = {}
        offset = 4
        for i in range(bindings_count):
            position = struct.unpack("I?", data[offset : offset + 5])
            offset += 5
            binding_count = struct.unpack("I", data[offset : offset + 4])[0]
            offset += 4
            binding = {}
            for _ in range(binding_count):
                p, u, d = struct.unpack("I?i", data[offset : offset + 12])
                offset += 12
                binding[(p, u)] = d
            bindings[position] = binding

        return bindings

    @staticmethod
    def deserialize(data: Tuple[bytes, ...]):
        number_of_picks_data, max_height_data, tumblers_data, bindings_data = data
        number_of_picks = struct.unpack("I", number_of_picks_data)[0]
        max_height = struct.unpack("I", max_height_data)[0]
        tumblers = Level.deserialize_tumblers(tumblers_data)
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
            tumblers = Level.deserialize_tumblers(tumblers_data)
            bindings = Level.deserialize_bindings(bindings_data)
            return Level(number_of_picks, max_height, tumblers, bindings)
