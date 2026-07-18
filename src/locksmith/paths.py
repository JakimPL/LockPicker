from pathlib import Path
from typing import Final

PACKAGE_ROOT: Final[Path] = Path(__file__).resolve().parent
REPOSITORY_ROOT: Final[Path] = PACKAGE_ROOT.parents[1]

CONFIG_DIRECTORY: Final[Path] = PACKAGE_ROOT / "config"
BUILD_DIRECTORY: Final[Path] = REPOSITORY_ROOT / "build"
BLEND_OUTPUT_PATH: Final[Path] = BUILD_DIRECTORY / "lockpicker.blend"
LOOKDEV_DIRECTORY: Final[Path] = REPOSITORY_ROOT / "docs" / "lookdev"
LOOKDEV_STILL_PATH: Final[Path] = LOOKDEV_DIRECTORY / "board_still.png"
THEMES_DIRECTORY: Final[Path] = REPOSITORY_ROOT / "assets" / "themes"
