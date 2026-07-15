from __future__ import annotations

from lockpicker.tumbler.definition import TumblerDefinition
from lockpicker.tumbler.location import Location
from tests.conftest import LockFactory


def define(
    position: int,
    *,
    upper: bool = False,
    group: int = 0,
    height: int = 5,
    post_release_height: int = 0,
    master: bool = True,
) -> TumblerDefinition:
    return TumblerDefinition(Location(position, upper), group, height, post_release_height, master)


def test_push_collapses_tumbler_and_wins(build_lock: LockFactory) -> None:
    lock = build_lock([define(0, height=5)])
    tumbler = lock.get_tumbler(Location(0, False))

    assert lock.check_win() is False
    lock.select_pick(0)
    lock.push(Location(0, False))

    assert tumbler.height == 1
    assert tumbler.free is True
    assert lock.check_win() is True


def test_push_blocked_while_lower_tumbler_is_raised(build_lock: LockFactory) -> None:
    lock = build_lock([define(0, group=0), define(1, group=1)], max_height=20)

    lock.select_pick(0)
    lock.push(Location(1, False))

    assert lock.get_tumbler(Location(1, False)).height == 5
    assert lock.get_pick(0) is None


def test_pushing_a_missing_location_is_a_no_op(build_lock: LockFactory) -> None:
    lock = build_lock([define(0, height=5)])

    lock.select_pick(0)
    lock.push(Location(99, False))

    assert lock.get_tumbler(Location(0, False)).height == 5
    assert lock.check_win() is False


def test_master_push_jams_the_whole_group(build_lock: LockFactory) -> None:
    lock = build_lock([define(0, group=0, master=True), define(1, group=0, height=3, master=False)])
    master = lock.get_tumbler(Location(0, False))
    member = lock.get_tumbler(Location(1, False))

    lock.select_pick(0)
    lock.push(Location(0, False))

    assert master.height == 1
    assert member.jammed is True
    assert member.height == 1
    assert lock.check_win() is True


def test_binding_propagates_difference_to_target(build_lock: LockFactory) -> None:
    lock = build_lock(
        [define(0, group=0, height=5), define(1, group=1, height=4)],
        max_height=20,
        bindings={Location(0, False): {Location(1, False): 2}},
    )
    target = lock.get_tumbler(Location(1, False))

    assert target.height == 4
    lock.select_pick(0)
    lock.push(Location(0, False))

    assert target.height == 6


def test_win_requires_every_tumbler_free(build_lock: LockFactory) -> None:
    lock = build_lock([define(0, group=0), define(1, group=1)], max_height=20)

    assert lock.check_win() is False
    lock.select_pick(0)
    lock.push(Location(0, False))
    assert lock.check_win() is False
    lock.push(Location(1, False))
    assert lock.check_win() is True


def test_load_state_restores_a_captured_snapshot(build_lock: LockFactory) -> None:
    lock = build_lock([define(0, height=5)])
    tumbler = lock.get_tumbler(Location(0, False))
    snapshot = lock.get_state()

    lock.select_pick(0)
    lock.push(Location(0, False))
    assert tumbler.height == 1

    lock.load_state(snapshot)
    assert tumbler.height == 5
    assert tumbler.pushed is False


def test_reset_restores_the_original_level(build_lock: LockFactory) -> None:
    lock = build_lock([define(0, height=5)])

    lock.select_pick(0)
    lock.push(Location(0, False))
    assert lock.get_tumbler(Location(0, False)).height == 1

    lock.reset()
    assert lock.get_tumbler(Location(0, False)).height == 5


def test_drain_snapshots_returns_history_and_keeps_the_last_state(build_lock: LockFactory) -> None:
    lock = build_lock([define(0, height=5)])
    lock.select_pick(0)
    lock.push(Location(0, False))

    snapshots = lock.drain_snapshots()
    assert len(snapshots) >= 2
    assert snapshots[-1][Location(0, False)] == 1
    assert len(lock.drain_snapshots()) == 1


def test_pick_selection_tracks_current_and_wraps(build_lock: LockFactory) -> None:
    lock = build_lock([define(0, height=5)], number_of_picks=2)

    assert lock.get_pick(0) is None
    lock.select_pick(1)
    assert lock.current_pick == 1
    lock.change_current_pick()
    assert lock.current_pick == 0


def test_possible_moves_lists_pushable_locations(build_lock: LockFactory) -> None:
    lock = build_lock([define(0, group=0), define(1, group=1)], max_height=20)

    moves = lock.get_possible_moves()

    assert Location(0, False) in moves
    assert Location(1, False) not in moves
