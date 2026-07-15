from dataclasses import replace
from typing import Dict, List, Optional, Tuple

from lockpicker.level.level import Level
from lockpicker.pick import PickSet
from lockpicker.state.state import LocatedTumblerState, PickState, State
from lockpicker.tumbler.location import Location
from lockpicker.tumbler.tumbler import Tumbler


class Lock:
    def __init__(self, level: Level):
        self._level = level
        self._level_copy = level.copy()
        self._validate_level()

        self._picks = PickSet(self.level.number_of_picks)
        self._states = [self._get_state()]

    def push(self, location: Location):
        tumbler = self.get_tumbler(location)
        self.release_current_pick()
        if self._can_push_tumbler(tumbler):
            self._push_tumbler(tumbler)

    def release_current_pick(self):
        location = self._picks.current_location()
        if location is not None:
            self._picks.clear()
            self._release_tumbler(location)
            self._revise_picks()

    def drain_snapshots(self) -> List[Dict[Location, int]]:
        snapshots = self._states
        self._states = [self._states[-1]]
        return snapshots

    def reset(self):
        self.level = self._level_copy

    def check_win(self) -> bool:
        for tumbler in self._level.tumblers.values():
            if tumbler is not None and not tumbler.free:
                return False

        return True

    def get_possible_moves(self) -> List[Tuple[int, bool]]:
        # TODO: consider state change after each move
        moves = []
        max_position = max([position for position, upper in self._level.tumblers])
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
        self._picks.change_current()

    def select_pick(self, pick: int):
        self._picks.select(pick)

    def get_tumbler(self, location: Location) -> Optional[Tumbler]:
        return self._level.tumblers.get(location)

    def get_tumblers_by_location(self) -> Dict[Location, Optional[Tumbler]]:
        return self._level.tumblers

    def _initialize_state(self):
        self._picks = PickSet(self.level.number_of_picks)
        self._states = [self._get_state()]

    def _can_push_tumbler(self, tumbler: Optional[Tumbler]) -> bool:
        return tumbler is not None and self._check_previous_tumblers(tumbler)

    def _push_tumbler(self, tumbler: Tumbler):
        location = tumbler.location
        self._picks.set_current(location)
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
        if not tumbler.jammed and not self._picks.other_picks(location):
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

    def _get_state(self) -> Dict[Location, int]:
        state: Dict[Location, int] = {}
        for location, tumbler in self._level.tumblers.items():
            if tumbler is not None:
                state[location] = tumbler.height

        return state

    def _add_current_state(self):
        self._states.append(self._get_state())

    def _apply_bindings(self, location: Location, pushed: bool):
        tumbler = self.get_tumbler(location)
        binding = self.level.bindings.get(location, {})
        for loc, difference in binding.items():
            picks = self._picks.other_picks(loc)
            tumb = self.get_tumbler(loc)

            jammed = False
            if picks and pushed:
                tumb.jam()
                jammed = True

            if not jammed:
                tumb.set_difference(difference if tumbler.pushed else 0, recalculate=not tumbler.jammed)
                if pushed and not tumbler.jammed:
                    tumb.release()

    def _apply_bindings_iteratively(self, location: Location, pushed: bool):
        self._apply_bindings(location, pushed)
        if not self._revise_picks():
            self._add_current_state()
            self._apply_bindings(location, pushed)

    def _apply_master_tumbler(self, tumbler: Tumbler):
        if tumbler.master and tumbler.pushed:
            for location in self._level.get_group(tumbler.group):
                tumb = self.get_tumbler(location)
                tumb.jam()
                tumb.set_difference(0)

        self._add_current_state()

    def _check_if_pick_is_valid(self, pick: int) -> bool:
        location = self._picks.get(pick)
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
                    self._picks.clear(pick)
                    self._release_tumbler(location)
                    self._add_current_state()

        return number_of_revisions == 1

    def _validate_level(self):
        self.level.validate()

    @property
    def current_pick(self) -> int:
        return self._picks.current

    def get_state(self) -> State:
        tumblers = tuple(
            LocatedTumblerState(location, replace(tumbler.state)) for location, tumbler in self._level.tumblers.items()
        )
        picks = tuple(PickState(pick, location) for pick, location in self._picks.items())
        return State(self.current_pick, tumblers, picks)

    def load_state(self, state: State):
        self._picks.select(state.current_pick)
        for location, tumbler_state in state.tumblers:
            tumbler = self.get_tumbler(location)
            tumbler.load_state(tumbler_state)

        for pick, location in state.picks:
            self._picks.set(pick, location)

    @property
    def level(self) -> Level:
        return self._level

    @level.setter
    def level(self, level: Level):
        self._level = level
        self._level_copy = level.copy()
        self._level.validate()
        self._initialize_state()
