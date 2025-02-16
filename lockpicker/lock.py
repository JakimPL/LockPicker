import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from lockpicker.level import Level
from lockpicker.location import Location
from lockpicker.tumbler import Tumbler


class Lock:
    def __init__(self, level: Level):
        self._level = level
        self._level_copy = level.copy()
        self._validate_level()

        self._groups = self._create_groups()
        self._locations = self._create_locations()
        self._picks = self._create_picks()

        self._current_pick = 0
        self._states = [self._get_state()]

    def push(self, location: Location):
        tumbler = self.get_tumbler(location)
        self.release_current_pick()
        if self._can_push_tumbler(tumbler):
            self._push_tumbler(tumbler)

    def release_current_pick(self):
        location = self._get_current_pick()
        if location is not None:
            self._clear_pick()
            self._release_tumbler(location)
            self._revise_picks()

    def add_tumbler(self, tumbler: Tumbler):
        if tumbler not in self.level.tumblers:
            self.level.add_tumbler(tumbler)
        self._add_tumbler_to_collections(tumbler)

    def delete_tumbler(self, tumbler: Tumbler):
        self._remove_tumbler_from_collections(tumbler)
        self.level.remove_tumbler(tumbler)

    def add_binding(self, initial_location: Location, target_location: Location, difference: int):
        self.level.add_binding(initial_location, target_location, difference)

    def get_recent_changes(self) -> List[Dict[Location, Tuple[int, int]]]:
        changes = []
        for i in range(len(self._states) - 1):
            current_state = self._states[i]
            next_state = self._states[i + 1]
            state_changes = {}
            for location, height in current_state.items():
                state_changes[location] = (height, next_state.get(location))

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
            self.push(move)

    def check_win(self) -> bool:
        for tumbler in self._locations.values():
            if tumbler is not None and not tumbler.free:
                return False

        return True

    def get_possible_moves(self) -> List[Tuple[int, bool]]:
        # TODO: consider state change after each move
        moves = []
        max_position = max([position for position, upper in self._locations.keys()])
        for upper in [True, False]:
            for position in reversed(range(max_position + 1)):
                tumbler = self.get_tumbler(Location(position, upper))
                if tumbler is not None and self._check_previous_tumblers(tumbler):
                    moves.extend([Location(pos, upper) for pos in range(position + 1)])
                    break

        return moves

    def get_pick(self, pick: int) -> Optional[Location]:
        return self._picks.get(pick)

    def change_current_pick(self):
        self._current_pick = (self._current_pick + 1) % self.level.number_of_picks

    def select_pick(self, pick: int):
        self._current_pick = pick

    def get_tumbler(self, location: Location) -> Optional[Tumbler]:
        return self._locations.get(location)

    def get_tumblers_by_group(self) -> Dict[int, List[Tumbler]]:
        return self._groups

    def get_tumblers_by_location(self) -> Dict[Location, Optional[Tumbler]]:
        return self._locations

    def _initialize_state(self):
        self._groups = self._create_groups()
        self._locations = self._create_locations()
        self._picks = self._create_picks()

        self._current_pick = 0
        self._states = [self._get_state()]

    def _create_groups(self) -> Dict[int, List[Tumbler]]:
        groups = defaultdict(list)
        for tumbler in self.level.tumblers:
            groups[tumbler.group].append(tumbler)

        return dict(groups.items())

    def _create_locations(self) -> Dict[Location, Optional[Tumbler]]:
        locations = {}
        for tumbler in self.level.tumblers:
            locations[tumbler.location] = tumbler

        return locations

    def _add_tumbler_to_collections(self, tumbler: Tumbler):
        self._groups.setdefault(tumbler.group, []).append(tumbler)
        self._locations[tumbler.location] = tumbler

    def _remove_tumbler_from_collections(self, tumbler: Tumbler):
        self._groups[tumbler.group].remove(tumbler)
        del self._locations[tumbler.location]

    def _can_push_tumbler(self, tumbler: Optional[Tumbler]) -> bool:
        return tumbler is not None and self._check_previous_tumblers(tumbler)

    def _push_tumbler(self, tumbler: Tumbler):
        location = tumbler.location
        self._set_current_pick(location)
        if tumbler.jammed:
            tumbler.unjam()
            return

        tumbler.unjam()
        tumbler.push()

        self._apply_bindings_iteratively(location, pushed=True)
        self._add_current_state()
        self._apply_master_tumbler(tumbler)

    def _release_tumbler(self, location: Location):
        tumbler = self.get_tumbler(location)
        if not tumbler.jammed and not self._get_other_picks(location):
            tumbler.release(direct=True)

        self._apply_bindings_iteratively(location, pushed=False)
        self._add_current_state()

    def _check_previous_tumblers(self, tumbler: Tumbler) -> bool:
        location = tumbler.location
        position = tumbler.position
        for i in range(position + 1):
            loc = Location(i, location.upper)
            tumb = self.get_tumbler(loc)
            counter = self.get_tumbler(loc.counter)
            if tumb is not None and i < position and not tumb.free:
                return False
            if counter is not None and tumbler.height + counter.height >= self.level.max_height:
                return False

        return True

    def _get_state(self):
        state = {}
        for location, tumbler in self._locations.items():
            if tumbler is not None:
                state[location] = tumbler.height

        return state

    def _add_current_state(self):
        self._states.append(self._get_state())

    def _apply_bindings(self, location: Location, pushed: bool):
        tumbler = self.get_tumbler(location)
        binding = self.level.bindings.get(location, {})
        for loc, difference in binding.items():
            picks = self._get_other_picks(loc)
            tumb = self.get_tumbler(loc)

            jammed = False
            if picks and pushed:
                tumb.jam()
                jammed = True

            if not jammed:
                tumb.set_difference(difference if tumbler.pushed else 0, not tumbler.jammed)
                if pushed and not tumbler.jammed:
                    tumb.release()

    def _apply_bindings_iteratively(self, location: Location, pushed: bool):
        self._apply_bindings(location, pushed)
        if not self._revise_picks():
            self._add_current_state()
            self._apply_bindings(location, pushed)

    def _apply_master_tumbler(self, tumbler: Tumbler):
        if tumbler.master and tumbler.pushed:
            for tumb in self._groups[tumbler.group]:
                tumb.jam()
                tumb.set_difference(0)

        self._add_current_state()

    def _create_picks(self) -> Dict[int, Optional[Location]]:
        return {pick: None for pick in range(self.level.number_of_picks)}

    def _get_current_pick(self) -> Optional[Location]:
        return self._picks[self._current_pick]

    def _set_current_pick(self, location: Location):
        self._picks[self._current_pick] = location

    def _get_other_picks(self, location: Location) -> List[int]:
        return [
            pick
            for pick, loc in self._picks.items()
            if loc is not None and loc == location and pick != self._current_pick
        ]

    def _check_if_pick_is_valid(self, pick: int) -> bool:
        location = self._picks[pick]
        if location is not None:
            position, upper = location
            for pos in range(position):
                loc = Location(pos, upper)
                tumbler = self.get_tumbler(loc)
                if tumbler is not None and not tumbler.free:
                    return False

        return True

    def _revise_picks(self) -> bool:
        all_picks_valid = False
        number_of_revisions = 0
        while not all_picks_valid:
            all_picks_valid = True
            number_of_revisions += 1
            for pick, location in self._picks.items():
                if not self._check_if_pick_is_valid(pick):
                    all_picks_valid = False
                    self._apply_bindings(location, False)
                    self._clear_pick(pick)
                    self._release_tumbler(location)
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
