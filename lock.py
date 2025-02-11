from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Tuple

from tumbler import Tumbler

MAX_HEIGHT = 11
PICKS = 2


class Lock:
    def __init__(
            self,
            tumblers: List[Tumbler],
            rules: Dict[Tuple[int, bool], List[Tuple[int, bool, int]]],
            number_of_picks: int = PICKS,
            max_height: int = MAX_HEIGHT
    ):
        self.tumblers = tumblers
        self.rules = rules
        self.max_height = max_height
        self.number_of_picks = number_of_picks

        self.validate_tumblers()
        self.groups = self.create_groups()
        self.positions = self.create_positions()
        self.picks = self.create_picks()

        self.current_pick = 0

    def validate_tumblers(self):
        assert all(tumbler.position >= 0 for tumbler in self.tumblers)
        assert all(0 < tumbler.base_height < self.max_height for tumbler in self.tumblers)

        tumblers = {
            (tumbler.group, tumbler.upper, tumbler.position)
            for tumbler in self.tumblers
        }

        assert len(tumblers) == len(self.tumblers)

        master_groups = defaultdict(list)
        for tumbler in self.tumblers:
            master_groups[tumbler.group].append(tumbler.master)

        for group, tumblers in master_groups.items():
            assert sum(tumblers) == 1

    def create_groups(self):
        groups = defaultdict(list)
        for tumbler in self.tumblers:
            groups[tumbler.group].append(tumbler)

        return dict(groups.items())

    def create_positions(self) -> Dict[int, Dict[int, Optional[Tumbler]]]:
        positions: DefaultDict[int, Dict[bool, Optional[Tumbler]]] = defaultdict(lambda: {True: None, False: None})
        last_position = 0
        for tumbler in self.tumblers:
            positions[tumbler.position][tumbler.upper] = tumbler
            if tumbler.position > last_position:
                last_position = tumbler.position

        return dict(positions.items())

    def create_picks(self) -> Dict[int, Optional[Tuple[int, bool]]]:
        return {pick: None for pick in range(self.number_of_picks)}

    def check_previous_tumblers(self, tumbler: Tumbler) -> bool:
        position = tumbler.position
        upper = tumbler.upper
        for i in range(position + 1):
            tumb = self.positions[i].get(upper)
            counter = self.positions[i].get(not upper)
            if tumb is not None and i < position and not tumb.pushed:
                return False
            if counter is not None and tumbler.height + counter.height >= self.max_height:
                return False

        return True

    def get_picks(self, position: int, upper: bool) -> List[int]:
        return [
            pick for pick, index in self.picks.items()
            if index is not None and index[0] == position and index[1] == upper
               and pick != self.current_pick
        ]

    def apply_rules(self, position: int, upper: bool, pushed: bool):
        tumbler = self.positions[position][upper]
        for pos, up, difference in self.rules.get((position, upper), []):
            picks = self.get_picks(pos, up)
            tumb = self.positions[pos][up]

            jammed = False
            if picks and pushed:
                tumb.jam()
                jammed = True

            if not jammed:
                tumb.difference = difference if tumbler.pushed else 0
                if pushed and not tumbler.jammed:
                    tumb.release()

    def apply_rules_iteratively(self, position: int, upper: bool, pushed: bool):
        self.apply_rules(position, upper, pushed)
        if not self.revise_picks():
            self.apply_rules(position, upper, pushed)

    def check_if_pick_is_valid(self, pick: int) -> bool:
        index = self.picks[pick]
        if index is not None:
            position, upper = index
            for pos in range(position):
                tumbler = self.positions[pos].get(upper)
                if tumbler is not None and tumbler.height > 1:
                    return False

            tumbler = self.positions[position][upper]
            if tumbler is not None and tumbler.height > 1:
                return False

        return True

    def revise_picks(self) -> bool:
        all_picks_valid = False
        number_of_revisions = 0
        while not all_picks_valid:
            all_picks_valid = True
            number_of_revisions += 1
            for pick, index in self.picks.items():
                if not self.check_if_pick_is_valid(pick):
                    all_picks_valid = False
                    position, upper = index
                    self.apply_rules(position, upper, False)
                    self.release_pick(pick)
                    self.release_tumbler(position, upper)

        return number_of_revisions == 1

    def push(self, position: int, upper: bool):
        tumbler = self.positions[position].get(upper)
        if tumbler is None or not self.check_previous_tumblers(tumbler):
            return

        self.picks[self.current_pick] = (position, upper)
        if tumbler.jammed:
            tumbler.unjam()
            return

        tumbler.unjam()
        tumbler.push()

        self.apply_rules_iteratively(position, upper, pushed=True)

        if tumbler.master and tumbler.pushed:
            for tumb in self.groups[tumbler.group]:
                tumb.jam()
                tumb.difference = 0

    def release_tumbler(self, position: int, upper: bool):
        tumbler = self.positions[position][upper]
        if not tumbler.jammed:
            tumbler.release()

        for pick in self.get_picks(position, upper):
            self.release_pick(pick)

        self.apply_rules_iteratively(position, upper, False)

    def release(self):
        current = self.picks[self.current_pick]
        if current is None:
            return

        position, upper = current
        self.release_pick()
        self.release_tumbler(position, upper)
        self.revise_picks()

    def release_pick(self, pick: Optional[int] = None):
        pick = pick if pick is not None else self.current_pick
        self.picks[pick] = None
