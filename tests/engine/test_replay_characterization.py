from __future__ import annotations

import json
from pathlib import Path

import pytest
from tests._characterization import (
    CHANGES_GOLDEN,
    REPLAY_GOLDEN,
    level_paths,
    replay_recent_changes,
    replay_state,
)

LEVEL_PATHS = level_paths()
LEVEL_IDS = [path.name for path in LEVEL_PATHS]

_REPLAY = json.loads(REPLAY_GOLDEN.read_text())
_CHANGES = json.loads(CHANGES_GOLDEN.read_text())


def test_golden_data_present() -> None:
    assert LEVEL_PATHS, "no level files found"
    assert set(_REPLAY) == {p.name for p in LEVEL_PATHS}
    assert set(_CHANGES) == {p.name for p in LEVEL_PATHS}


@pytest.mark.parametrize("path", LEVEL_PATHS, ids=LEVEL_IDS)
def test_scripted_replay_matches_golden(path: Path) -> None:
    assert replay_state(path) == _REPLAY[path.name]


@pytest.mark.parametrize("path", LEVEL_PATHS, ids=LEVEL_IDS)
def test_recent_changes_sequence_matches_golden(path: Path) -> None:
    assert replay_recent_changes(path) == _CHANGES[path.name]
