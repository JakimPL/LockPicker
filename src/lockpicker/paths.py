from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT: Path = Path(__file__).resolve().parent
PROJECT_ROOT: Path = PACKAGE_ROOT.parent.parent

LEVELS_DIR: Path = PROJECT_ROOT / "levels"
CONFIG_FILE: Path = PROJECT_ROOT / "config.yaml"
