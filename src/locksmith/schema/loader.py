from pathlib import Path
from typing import Dict, Final

import yaml

from locksmith.schema.models.scene import SceneConfig

_FRAGMENT_SUFFIX: Final[str] = ".yaml"


def load_scene_config(directory: Path) -> SceneConfig:
    """Assemble the scene description from a directory of YAML fragments.

    Every fragment's top-level keys merge into the mapping of the directory
    that holds it, so files group related sections while the keys alone define
    the structure; subdirectories nest as the key of their own name. A key
    collision raises, so every value has exactly one home.
    """
    return SceneConfig.model_validate(_load_directory(directory))


def _load_directory(directory: Path) -> Dict[str, object]:
    merged: Dict[str, object] = {}
    for entry in sorted(directory.iterdir()):
        if entry.is_dir():
            _merge_key(merged, entry.name, _load_directory(entry), source=entry)
        elif entry.suffix == _FRAGMENT_SUFFIX:
            for key, value in _load_fragment(entry).items():
                _merge_key(merged, key, value, source=entry)

    return merged


def _load_fragment(path: Path) -> Dict[str, object]:
    """Read one YAML fragment.

    Raises:
        TypeError: when the fragment holds anything other than a mapping.
    """
    with path.open(encoding="utf-8") as stream:
        raw: object = yaml.safe_load(stream)

    if not isinstance(raw, dict):
        raise TypeError(f"{path} must hold a top-level mapping")

    return raw


def _merge_key(
    merged: Dict[str, object],
    key: str,
    value: object,
    *,
    source: Path,
) -> None:
    """Add one key to the directory mapping.

    Raises:
        ValueError: when another fragment or subdirectory already owns the key.
    """
    if key in merged:
        raise ValueError(f"config key {key!r} from {source} is already defined elsewhere")

    merged[key] = value
