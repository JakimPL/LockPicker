import gzip
import os
import struct
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union

from tumbler import Tumbler


@dataclass
class Level:
    number_of_picks: int
    max_height: int
    tumblers: List[Tumbler]
    rules: Dict[Tuple[int, bool], List[Tuple[int, bool, int]]]

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

    def save(self, filepath: Union[str, os.PathLike]):
        with gzip.open(filepath, "wb") as file:
            number_of_picks = struct.pack("I", self.number_of_picks)
            max_height = struct.pack("I", self.max_height)
            serialized_tumblers = self.serialize_tumblers()
            serialized_rules = self.serialize_rules()

            file.write(number_of_picks)
            file.write(max_height)
            file.write(serialized_tumblers)
            file.write(serialized_rules)

    @staticmethod
    def deserialize_tumblers(file: gzip.GzipFile) -> List[Tumbler]:
        tumblers_count = struct.unpack("I", file.read(4))[0]
        tumblers = []
        for _ in range(tumblers_count):
            tumbler_data = file.read(struct.calcsize(Tumbler.struct_format))
            tumbler = Tumbler.deserialize(tumbler_data)
            tumblers.append(tumbler)

        return tumblers

    @staticmethod
    def deserialize_rules(
        file: gzip.GzipFile,
    ) -> Dict[Tuple[int, bool], List[Tuple[int, bool, int]]]:
        rules_count = struct.unpack("I", file.read(4))[0]
        rules = {}
        for _ in range(rules_count):
            position = struct.unpack("I?", file.read(5))
            rule_count = struct.unpack("I", file.read(4))[0]
            rule_list = []
            for _ in range(rule_count):
                rule = struct.unpack("I?i", file.read(12))
                rule_list.append(rule)
            rules[position] = rule_list

        return rules

    @staticmethod
    def load(filepath: Union[str, os.PathLike]) -> "Level":
        with gzip.open(filepath, "rb") as file:
            number_of_picks = struct.unpack("I", file.read(4))[0]
            max_height = struct.unpack("I", file.read(4))[0]
            tumblers = Level.deserialize_tumblers(file)
            rules = Level.deserialize_rules(file)
            return Level(number_of_picks, max_height, tumblers, rules)
