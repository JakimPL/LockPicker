from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Tuple

from lockpicker.level import Level
from lockpicker.tumbler import Tumbler


class Lock:
    def __init__(self, level: Level):
        self._level = level
        self.level.validate()
        self.groups = self._create_groups()
        self.positions = self._create_positions()
        self.picks = self._create_picks()

        self.current_pick = 0
        self.changes = []

    def push(self, position: int, upper: bool):
        tumbler = self.positions[position].get(upper)
        if tumbler is None or not self._check_previous_tumblers(tumbler):
            return

        height = tumbler.height
        self.picks[self.current_pick] = (position, upper)
        if tumbler.jammed:
            tumbler.unjam()
            return

        tumbler.unjam()
        tumbler.push()

        self._add_change(tumbler, height)
        self._apply_bindings_iteratively(position, upper, pushed=True)
        self._apply_master_tumbler(tumbler)

    def release_current_pick(self):
        current = self.picks[self.current_pick]
        if current is None:
            return

        position, upper = current
        self._clear_pick()
        self._release_tumbler(position, upper)
        self._revise_picks()

    def add_tumbler(self, tumbler: Tumbler):
        if tumbler not in self.level.tumblers:
            self.level.add_tumbler(tumbler)
        if tumbler.group not in self.groups:
            self.groups[tumbler.group] = []
        self.groups[tumbler.group].append(tumbler)

        if tumbler.position not in self.positions:
            self.positions[tumbler.position] = {}
        self.positions[tumbler.position][tumbler.upper] = tumbler

    def delete_tumbler(self, tumbler: Tumbler):
        position = tumbler.position
        upper = tumbler.upper
        self.groups[tumbler.group].remove(tumbler)
        self.positions[position][upper] = None
        self.level.remove_tumbler(tumbler)

    def add_binding(self, initial_pos: int, initial_up: bool, target_pos: int, target_up: bool, difference: int):
        self.level.add_binding(initial_pos, initial_up, target_pos, target_up, difference)

    def get_recent_changes(self) -> Dict[Tuple[int, bool], Tuple[int, int]]:
        changes = self.changes.copy()
        self.changes.clear()
        return {(pos, up): (start, end) for pos, up, start, end in changes}

    def check_win(self) -> bool:
        for items in self.positions.values():
            for tumbler in items.values():
                if tumbler is not None and tumbler.height > 1:
                    return False

        return True

    def get_possible_moves(self) -> List[Tuple[int, bool]]:
        moves = []
        for upper in [True, False]:
            for position in reversed(sorted(self.positions)):
                tumbler = self.positions[position].get(upper)
                if tumbler is not None and self._check_previous_tumblers(tumbler):
                    moves.extend([(pos, upper) for pos in range(position + 1)])
                    break

        return moves

    def change_current_pick(self):
        self.current_pick = (self.current_pick + 1) % self.level.number_of_picks

    def _create_groups(self):
        groups = defaultdict(list)
        for tumbler in self.level.tumblers:
            groups[tumbler.group].append(tumbler)

        return dict(groups.items())

    def _create_positions(self) -> Dict[int, Dict[int, Optional[Tumbler]]]:
        positions: DefaultDict[int, Dict[bool, Optional[Tumbler]]] = defaultdict(lambda: {True: None, False: None})
        last_position = 0
        for tumbler in self.level.tumblers:
            positions[tumbler.position][tumbler.upper] = tumbler
            if tumbler.position > last_position:
                last_position = tumbler.position

        return dict(positions.items())

    def _create_picks(self) -> Dict[int, Optional[Tuple[int, bool]]]:
        return {pick: None for pick in range(self.level.number_of_picks)}

    def _check_previous_tumblers(self, tumbler: Tumbler) -> bool:
        position = tumbler.position
        upper = tumbler.upper
        for i in range(position + 1):
            if i not in self.positions:
                continue
            tumb = self.positions[i].get(upper)
            counter = self.positions[i].get(not upper)
            if tumb is not None and i < position and tumb.height > 1:
                return False
            if counter is not None and tumbler.height + counter.height >= self.level.max_height:
                return False

        return True

    def _get_picks(self, position: int, upper: bool) -> List[int]:
        return [
            pick
            for pick, index in self.picks.items()
            if index is not None and index[0] == position and index[1] == upper and pick != self.current_pick
        ]

    def _add_change(self, tumbler: Tumbler, height: int):
        if tumbler.height != height:
            self.changes.append((tumbler.position, tumbler.upper, height, tumbler.height))

    def _apply_bindings(self, position: int, upper: bool, pushed: bool):
        tumbler = self.positions[position][upper]
        binding = self.level.bindings.get((position, upper), {})
        for (pos, up), difference in binding.items():
            picks = self._get_picks(pos, up)
            tumb = self.positions[pos][up]
            height = tumb.height

            jammed = False
            if picks and pushed:
                tumb.jam()
                jammed = True

            if not jammed:
                tumb.difference = difference if tumbler.pushed else 0
                if pushed and not tumbler.jammed:
                    tumb.release()

            self._add_change(tumb, height)

    def _apply_bindings_iteratively(self, position: int, upper: bool, pushed: bool):
        self._apply_bindings(position, upper, pushed)
        if not self._revise_picks():
            self._apply_bindings(position, upper, pushed)

    def _apply_master_tumbler(self, tumbler: Tumbler):
        if tumbler.master and tumbler.pushed:
            for tumb in self.groups[tumbler.group]:
                height = tumb.height
                tumb.jam()
                tumb.difference = 0
                self._add_change(tumb, height)

    def _release_tumbler(self, position: int, upper: bool):
        tumbler = self.positions[position][upper]
        height = tumbler.height
        if not tumbler.jammed and not self._get_picks(position, upper):
            tumbler.release(direct=True)

        self._add_change(tumbler, height)
        self._apply_bindings_iteratively(position, upper, False)

    def _check_if_pick_is_valid(self, pick: int) -> bool:
        index = self.picks[pick]
        if index is not None:
            position, upper = index
            for pos in range(position):
                if pos not in self.positions:
                    continue

                tumbler = self.positions[pos].get(upper)
                if tumbler is not None and tumbler.height > 1:
                    return False

            tumbler = self.positions[position][upper]
            if tumbler is not None and tumbler.height > 1:
                return False

        return True

    def _revise_picks(self) -> bool:
        all_picks_valid = False
        number_of_revisions = 0
        while not all_picks_valid:
            all_picks_valid = True
            number_of_revisions += 1
            for pick, index in self.picks.items():
                if not self._check_if_pick_is_valid(pick):
                    all_picks_valid = False
                    position, upper = index
                    self._apply_bindings(position, upper, False)
                    self._clear_pick(pick)
                    self._release_tumbler(position, upper)

        return number_of_revisions == 1

    def _clear_pick(self, pick: Optional[int] = None):
        pick = pick if pick is not None else self.current_pick
        self.picks[pick] = None

    @property
    def level(self) -> Level:
        return self._level

    @level.setter
    def level(self, level: Level):
        self._level = level
        self.level.validate()
        self.groups = self._create_groups()
        self.positions = self._create_positions()
        self.picks = self._create_picks()

        self.current_pick = 0
        self.changes = []
