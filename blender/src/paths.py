from pathlib import Path
from typing import Final

BLENDER_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT: Final[Path] = BLENDER_ROOT.parent

CONFIG_DIRECTORY: Final[Path] = BLENDER_ROOT / "config"
BLEND_OUTPUT_PATH: Final[Path] = BLENDER_ROOT / "lockpicker.blend"
LOOKDEV_DIRECTORY: Final[Path] = REPOSITORY_ROOT / "docs" / "lookdev"
LOOKDEV_STILL_PATH: Final[Path] = LOOKDEV_DIRECTORY / "board_still.png"
THEMES_DIRECTORY: Final[Path] = REPOSITORY_ROOT / "assets" / "themes"
