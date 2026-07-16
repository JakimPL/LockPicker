from __future__ import annotations

from pathlib import Path

import pytest
from lockpicker.level.level import Level
from tests._characterization import level_paths

LEVEL_PATHS = level_paths()
LEVEL_IDS = [path.name for path in LEVEL_PATHS]


@pytest.mark.parametrize("path", LEVEL_PATHS, ids=LEVEL_IDS)
def test_save_load_roundtrip_is_byte_stable(path: Path, tmp_path: Path) -> None:
    level = Level.load(path)
    out = tmp_path / path.name
    level.save(out)
    reloaded = Level.load(out)
    assert level.serialize() == reloaded.serialize()


@pytest.mark.parametrize("path", LEVEL_PATHS, ids=LEVEL_IDS)
def test_serialize_is_deterministic(path: Path) -> None:
    level = Level.load(path)
    assert level.serialize() == level.serialize()


@pytest.mark.parametrize("path", LEVEL_PATHS, ids=LEVEL_IDS)
def test_leveldata_codec_roundtrip(path: Path) -> None:
    level = Level.load(path)
    data = level.serialize()
    restored = level.deserialize(data)
    assert restored.serialize() == data


@pytest.mark.parametrize("path", LEVEL_PATHS, ids=LEVEL_IDS)
def test_loaded_authored_fields_are_stable(path: Path) -> None:
    level = Level.load(path)
    assert level.number_of_picks >= 1
    assert level.max_height >= 3
    for location, tumbler in level.tumblers.items():
        assert tumbler.location == location
        assert 0 < tumbler.base_height <= level.max_height
        assert tumbler.group >= 0
