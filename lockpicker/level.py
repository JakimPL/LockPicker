import gzip
import os
import struct
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
    rules: Dict[Tuple[int, bool], List[Tuple[int, bool, int]]]

    @staticmethod
    def default() -> "Level":
        return Level(NUMBER_OF_PICKS, MAX_HEIGHT, [], {})

    def copy(self) -> "Level":
        tumblers = [tumbler.copy() for tumbler in self.tumblers]
        rules = {position: rules.copy() for position, rules in self.rules.items()}
        return Level(
            self.number_of_picks,
            self.max_height,
            tumblers,
            rules,
        )

    def serialize_tumblers(self) -> bytes:
        tumblers_count = struct.pack("I", len(self.tumblers))
        tumblers_data = b"".join(tumbler.serialize() for tumbler in self.tumblers)
        return tumblers_count + tumblers_data

    def serialize_rules(self) -> bytes:
        rules_data = struct.pack("I", len(self.rules))
        for position, rules in self.rules.items():
            rules_data += struct.pack("I?", *position)
            rules_data += struct.pack("I", len(rules))
            for rule in rules:
                rules_data += struct.pack("I?i", *rule)

        return rules_data

    def serialize(self) -> Tuple[bytes, ...]:
        number_of_picks = struct.pack("I", self.number_of_picks)
        max_height = struct.pack("I", self.max_height)
        serialized_tumblers = self.serialize_tumblers()
        serialized_rules = self.serialize_rules()
        return (
            number_of_picks, max_height, serialized_tumblers, serialized_rules
        )

    def save(self, filepath: Union[str, os.PathLike]):
        with gzip.open(filepath, "wb") as file:
            number_of_picks, max_height, serialized_tumblers, serialized_rules = self.serialize()
            tumblers_block_size = struct.pack("I", len(serialized_tumblers))
            rules_block_size = struct.pack("I", len(serialized_tumblers))
            file.write(number_of_picks)
            file.write(max_height)
            file.write(tumblers_block_size)
            file.write(serialized_tumblers)
            file.write(rules_block_size)
            file.write(serialized_rules)
            print(f"Level saved to {filepath}.")

    @staticmethod
    def deserialize_tumblers(data: bytes) -> List[Tumbler]:
        tumblers_count = struct.unpack("I", data[:4])[0]
        tumblers = []
        size = struct.calcsize(Tumbler.struct_format)
        for i in range(tumblers_count):
            tumbler_data = data[4 + i * size: 4 + (i + 1) * size]
            tumbler = Tumbler.deserialize(tumbler_data)
            tumblers.append(tumbler)

        return tumblers

    @staticmethod
    def deserialize_rules(data: bytes) -> Dict[Tuple[int, bool], List[Tuple[int, bool, int]]]:
        rules_count = struct.unpack("I", data[:4])[0]
        rules = {}
        offset = 4
        for i in range(rules_count):
            position = struct.unpack("I?", data[offset:offset + 5])
            offset += 5
            rule_count = struct.unpack("I", data[offset:offset + 4])[0]
            offset += 4
            rule_list = []
            for _ in range(rule_count):
                rule = struct.unpack("I?i", data[offset:offset + 12])
                offset += 12
                rule_list.append(rule)
            rules[position] = rule_list

        return rules

    @staticmethod
    def deserialize(data: Tuple[bytes, ...]):
        number_of_picks_data, max_height_data, tumblers_data, rules_data = data
        number_of_picks = struct.unpack("I", number_of_picks_data)[0]
        max_height = struct.unpack("I", max_height_data)[0]
        tumblers = Level.deserialize_tumblers(tumblers_data)
        rules = Level.deserialize_rules(rules_data)
        return Level(number_of_picks, max_height, tumblers, rules)

    @staticmethod
    def load(filepath: Union[str, os.PathLike]) -> "Level":
        with gzip.open(filepath, "rb") as file:
            number_of_picks_data = file.read(4)
            max_height_data = file.read(4)
            tumblers_block_size = struct.unpack("I", file.read(4))[0]
            tumblers_data = file.read(tumblers_block_size)
            rules_block_size = struct.unpack("I", file.read(4))[0]
            rules_data = file.read(rules_block_size)

            number_of_picks = struct.unpack("I", number_of_picks_data)[0]
            max_height = struct.unpack("I", max_height_data)[0]
            tumblers = Level.deserialize_tumblers(tumblers_data)
            rules = Level.deserialize_rules(rules_data)
            return Level(number_of_picks, max_height, tumblers, rules)
