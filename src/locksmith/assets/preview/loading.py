from pathlib import Path
from typing import Dict

from locksmith.assets.manifest.theme import ThemeManifest
from locksmith.blender.images import read_rgba_pixels
from locksmith.types import RGBAImage


def _load_sprites(
    manifest: ThemeManifest,
    directory: Path,
) -> Dict[str, RGBAImage]:
    filenames = {manifest.board.background, manifest.board.frame, manifest.badges.master.image}
    for orientation in (manifest.tumblers.upper, manifest.tumblers.lower):
        filenames.update(orientation.images.values())
        filenames.add(orientation.shadow.image)
    filenames.update(pick.image for pick in manifest.picks.values())
    filenames.update((manifest.lips.upper.image, manifest.lips.lower.image))
    return {filename: read_rgba_pixels(directory / filename) for filename in sorted(filenames)}
