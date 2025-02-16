import random
from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Tuple

from lockpicker.level import Level
from lockpicker.tumbler import Tumbler


class Lock:
    def __init__(self, level: Level):
        self._level = level
        self._level_copy = level.copy()
        self._validate_level()

        self._groups = self._create_groups()
        self._positions = self._create_positions()
        self._picks = self._create_picks()

        self._current_pick = 0
        self._states = [self._get_state()]

    def push(self, position: int, upper: bool):
        tumbler = self.get_tumbler(position, upper)
        self.release_current_pick()
        if self._can_push_tumbler(tumbler):
            self._push_tumbler(tumbler)

    def release_current_pick(self):
        current = self._get_current_pick()
        if current is not None:
            self._clear_pick()
            self._release_tumbler(*current)
            self._revise_picks()

    def add_tumbler(self, tumbler: Tumbler):
        if tumbler not in self.level.tumblers:
            self.level.add_tumbler(tumbler)
        self._add_tumbler_to_collections(tumbler)

    def delete_tumbler(self, tumbler: Tumbler):
        self._remove_tumbler_from_collections(tumbler)
        self.level.remove_tumbler(tumbler)

    def add_binding(self, initial_pos: int, initial_up: bool, target_pos: int, target_up: bool, difference: int):
        self.level.add_binding(initial_pos, initial_up, target_pos, target_up, difference)

    def get_recent_changes(self) -> List[Dict[Tuple[int, bool], Tuple[int, int]]]:
        changes = []
        for i in range(len(self._states) - 1):
            current_state = self._states[i]
            next_state = self._states[i + 1]
            state_changes = {}
            for (pos, up), height in current_state.items():
                state_changes[(pos, up)] = (height, next_state.get((pos, up)))

            if state_changes:
                changes.append(state_changes)

        self._states = [self._states[-1]]
        return list(reversed(changes))

    def reset(self):
        self.level = self._level_copy

    def play_random_move(self):
        moves = self.get_possible_moves()
        if moves:
            move = random.choice(moves)
            pick = random.choice(range(self.level.number_of_picks))
            self.select_pick(pick)
            self.push(*move)

    def check_win(self) -> bool:
        for items in self._positions.values():
            for tumbler in items.values():
                if tumbler is not None and tumbler.height > 1:
                    return False

        return True

    def get_possible_moves(self) -> List[Tuple[int, bool]]:
        # TODO: consider state change after each move
        moves = []
        for upper in [True, False]:
            for position in reversed(sorted(self._positions)):
                tumbler = self._positions[position].get(upper)
                if tumbler is not None and self._check_previous_tumblers(tumbler):
                    moves.extend([(pos, upper) for pos in range(position + 1)])
                    break

        return moves

    def get_pick(self, pick: int) -> Optional[Tuple[int, bool]]:
        return self._picks.get(pick)

    def change_current_pick(self):
        self._current_pick = (self._current_pick + 1) % self.level.number_of_picks

    def select_pick(self, pick: int):
        self._current_pick = pick

    def get_tumbler(self, position: int, upper: bool) -> Optional[Tumbler]:
        return self._positions.get(position, {}).get(upper)

    def get_tumblers_by_group(self) -> Dict[int, List[Tumbler]]:
        return self._groups

    def get_tumblers_by_position(self) -> Dict[int, Dict[bool, Optional[Tumbler]]]:
        return self._positions

    def _initialize_state(self):
        self._groups = self._create_groups()
        self._positions = self._create_positions()
        self._picks = self._create_picks()

        self._current_pick = 0
        self._states = [self._get_state()]

    def _create_groups(self):
        groups = defaultdict(list)
        for tumbler in self.level.tumblers:
            groups[tumbler.group].append(tumbler)

        return dict(groups.items())

    def _create_positions(self) -> Dict[int, Dict[bool, Optional[Tumbler]]]:
        positions: DefaultDict[int, Dict[bool, Optional[Tumbler]]] = defaultdict(lambda: {True: None, False: None})
        for tumbler in self.level.tumblers:
            positions[tumbler.position][tumbler.upper] = tumbler

        return dict(positions.items())

    def _add_tumbler_to_collections(self, tumbler: Tumbler):
        self._groups.setdefault(tumbler.group, []).append(tumbler)
        self._positions.setdefault(tumbler.position, {})[tumbler.upper] = tumbler

    def _remove_tumbler_from_collections(self, tumbler: Tumbler):
        self._groups[tumbler.group].remove(tumbler)
        self._positions[tumbler.position][tumbler.upper] = None

    def _can_push_tumbler(self, tumbler: Optional[Tumbler]) -> bool:
        return tumbler is not None and self._check_previous_tumblers(tumbler)

    def _push_tumbler(self, tumbler: Tumbler):
        position = tumbler.position
        upper = tumbler.upper
        self._set_current_pick(position, upper)
        if tumbler.jammed:
            tumbler.unjam()
            return

        tumbler.unjam()
        tumbler.push()

        self._apply_bindings_iteratively(position, upper, pushed=True)
        self._add_current_state()
        self._apply_master_tumbler(tumbler)

    def _release_tumbler(self, position: int, upper: bool):
        tumbler = self._positions[position][upper]
        if not tumbler.jammed and not self._get_other_picks(position, upper):
            tumbler.release(direct=True)

        self._apply_bindings_iteratively(position, upper, False)
        self._add_current_state()

    def _check_previous_tumblers(self, tumbler: Tumbler) -> bool:
        position = tumbler.position
        upper = tumbler.upper
        for i in range(position + 1):
            if i not in self._positions:
                continue
            tumb = self._positions[i].get(upper)
            counter = self._positions[i].get(not upper)
            if tumb is not None and i < position and tumb.height > 1:
                return False
            if counter is not None and tumbler.height + counter.height >= self.level.max_height:
                return False

        return True

    def _get_state(self):
        state = {}
        for position, items in self._positions.items():
            for upper, tumbler in items.items():
                if tumbler is not None:
                    state[(position, upper)] = tumbler.height

        return state

    def _add_current_state(self):
        self._states.append(self._get_state())

    def _apply_bindings(self, position: int, upper: bool, pushed: bool):
        tumbler = self._positions[position][upper]
        binding = self.level.bindings.get((position, upper), {})
        for (pos, up), difference in binding.items():
            picks = self._get_other_picks(pos, up)
            tumb = self._positions[pos][up]

            jammed = False
            if picks and pushed:
                tumb.jam()
                jammed = True

            if not jammed:
                tumb.set_difference(difference if tumbler.pushed else 0, not tumbler.jammed)
                if pushed and not tumbler.jammed:
                    tumb.release()

    def _apply_bindings_iteratively(self, position: int, upper: bool, pushed: bool):
        self._apply_bindings(position, upper, pushed)
        if not self._revise_picks():
            self._add_current_state()
            self._apply_bindings(position, upper, pushed)

    def _apply_master_tumbler(self, tumbler: Tumbler):
        if tumbler.master and tumbler.pushed:
            for tumb in self._groups[tumbler.group]:
                tumb.jam()
                tumb.set_difference(0)

        self._add_current_state()

    def _create_picks(self) -> Dict[int, Optional[Tuple[int, bool]]]:
        return {pick: None for pick in range(self.level.number_of_picks)}

    def _get_current_pick(self) -> Optional[Tuple[int, bool]]:
        return self._picks[self._current_pick]

    def _set_current_pick(self, position: int, upper: bool):
        self._picks[self._current_pick] = (position, upper)

    def _get_other_picks(self, position: int, upper: bool) -> List[int]:
        return [
            pick
            for pick, index in self._picks.items()
            if index is not None and index[0] == position and index[1] == upper and pick != self._current_pick
        ]

    def _check_if_pick_is_valid(self, pick: int) -> bool:
        index = self._picks[pick]
        if index is not None:
            position, upper = index
            for pos in range(position):
                if pos not in self._positions:
                    continue

                tumbler = self._positions[pos].get(upper)
                if tumbler is not None and tumbler.height > 1:
                    return False

            tumbler = self._positions[position][upper]
            if tumbler is not None and tumbler.height > 1:
                return False

        return True

    def _revise_picks(self) -> bool:
        all_picks_valid = False
        number_of_revisions = 0
        while not all_picks_valid:
            all_picks_valid = True
            number_of_revisions += 1
            for pick, index in self._picks.items():
                if not self._check_if_pick_is_valid(pick):
                    all_picks_valid = False
                    position, upper = index
                    self._apply_bindings(position, upper, False)
                    self._clear_pick(pick)
                    self._release_tumbler(position, upper)
                    self._add_current_state()

        return number_of_revisions == 1

    def _clear_pick(self, pick: Optional[int] = None):
        pick = pick if pick is not None else self._current_pick
        self._picks[pick] = None

    def _validate_level(self):
        self.level.validate()

    @property
    def current_pick(self) -> int:
        return self._current_pick

    @property
    def level(self) -> Level:
        return self._level

    @level.setter
    def level(self, level: Level):
        self._level = level
        self._level_copy = level.copy()
        self._level.validate()
        self._initialize_state()
