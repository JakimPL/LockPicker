from pathlib import Path

from locksmith.assets.batch.constants import _BACKGROUND_FILENAME, _FRAME_FILENAME
from locksmith.assets.batch.sprite import _render_file, _scaled, _set_canvas
from locksmith.assets.manifest.board import BoardAssets
from locksmith.blender.scene_state import camera_ray_visible, film_transparent
from locksmith.builder import WorkshopScene
from locksmith.schema.models.scene import SceneConfig
from locksmith.types import PixelPair


def _render_board(
    workshop: WorkshopScene,
    *,
    config: SceneConfig,
    directory: Path,
) -> BoardAssets:
    """Render the opaque back layer and the transparent overlay plate.

    The back layer is the empty mechanism: the diffuse channel wall carries
    the plate's static shadowing even though the plate itself stays out of
    the image, so pins composite over exactly the wall the still shows
    around them.
    """
    logical = _logical_board_size(config)
    scale = config.assets.image_scale
    scene = workshop.scene
    scene.camera = workshop.board_camera
    _set_canvas(scene, size=logical, image_scale=scale)

    with camera_ray_visible(workshop.background_wall), film_transparent(scene, transparent=False):
        _render_file(scene, directory / _BACKGROUND_FILENAME, expected=_scaled(logical, scale))

    statics = (
        workshop.frame_plate,
        workshop.bench,
        workshop.keyway,
        workshop.flanges,
        workshop.screws,
    )
    with camera_ray_visible(*statics), film_transparent(scene, transparent=True):
        _render_file(scene, directory / _FRAME_FILENAME, expected=_scaled(logical, scale))

    return BoardAssets(
        logical_size=logical,
        background=_BACKGROUND_FILENAME,
        frame=_FRAME_FILENAME,
    )


def _logical_board_size(config: SceneConfig) -> PixelPair:
    """The board size as whole pixels.

    Raises:
        ValueError: when the configured board size is fractional.
    """
    width = config.board.width_pixels
    height = config.board.height_pixels
    if not width.is_integer() or not height.is_integer():
        raise ValueError(f"board size {width}x{height} is not a whole pixel count")
    return int(width), int(height)
