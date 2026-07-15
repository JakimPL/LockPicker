from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple, Union

from lockpicker.engine.lock import Lock
from lockpicker.game.animation import compute_animation_steps
from lockpicker.level.level import Level
from lockpicker.paths import LEVELS_DIR
from lockpicker.tumbler.location import Location

DATA_DIR = Path(__file__).resolve().parent / "data"
REPLAY_GOLDEN = DATA_DIR / "replay_golden.json"
CHANGES_GOLDEN = DATA_DIR / "recent_changes_golden.json"


def level_paths() -> List[Path]:
    return sorted(LEVELS_DIR.glob("*.lvl"))


def _key(location: Location) -> str:
    return f"{location.position}:{int(location.upper)}"


def scripted_moves(level: Level) -> List[Tuple[str, Union[int, Location]]]:
    moves: List[Tuple[str, Union[int, Location]]] = []
    for pick in range(level.number_of_picks):
        moves.append(("select", pick))
        for location in sorted(level.tumblers.keys()):
            moves.append(("push", location))

    return moves


def replay_state(path: Path) -> Dict[str, Union[Dict[str, int], bool]]:
    level = Level.load(path)
    lock = Lock(level)
    for kind, arg in scripted_moves(level):
        if kind == "select" and isinstance(arg, int):
            lock.select_pick(arg)
        elif isinstance(arg, Location):
            lock.push(arg)

    heights = {_key(loc): tumbler.height for loc, tumbler in sorted(level.tumblers.items())}
    return {"heights": heights, "win": lock.check_win()}


def _probe_location(level: Level) -> Location:
    if level.bindings:
        return sorted(level.bindings.keys())[0]

    return sorted(level.tumblers.keys())[0]


def replay_recent_changes(path: Path) -> List[Dict[str, List[int]]]:
    level = Level.load(path)
    lock = Lock(level)
    lock.select_pick(0)
    lock.push(_probe_location(level))
    steps = compute_animation_steps(lock.drain_snapshots())
    return [{_key(loc): list(pair) for loc, pair in step.items()} for step in steps]


def _generate() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    replay = {path.name: replay_state(path) for path in level_paths()}
    changes = {path.name: replay_recent_changes(path) for path in level_paths()}
    REPLAY_GOLDEN.write_text(json.dumps(replay, indent=2, sort_keys=True) + "\n")
    CHANGES_GOLDEN.write_text(json.dumps(changes, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {REPLAY_GOLDEN} ({len(replay)} levels)")
    print(f"Wrote {CHANGES_GOLDEN} ({len(changes)} levels)")


if __name__ == "__main__":
    _generate()
