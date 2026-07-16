import math
from typing import Final

from bpy.types import Collection, Object

from locksmith.blender.cameras import new_orthographic_camera
from locksmith.board import BoardGeometry
from locksmith.config.models.views.views import ViewsConfig
from locksmith.types import Vec3

_BOARD_CAMERA_NAME: Final[str] = "CAM_BOARD"
_SPRITE_CAMERA_PREFIX: Final[str] = "CAM_"
_FACING_BOARD: Final[Vec3] = (math.pi / 2, 0.0, 0.0)


def build_cameras(*, views: ViewsConfig, board: BoardGeometry, collection: Collection) -> Object:
    """One orthographic camera per framing, all looking straight down +y.

    Orthographic projection is a firm requirement: sprites translate across
    the board at runtime and only a perspective-free view keeps them valid at
    every position. The board camera fills the frame with the board; sprite
    cameras frame the parked prototypes.
    """
    board_camera = new_orthographic_camera(
        _BOARD_CAMERA_NAME,
        location=(0.0, views.camera_y, 0.0),
        rotation_radians=_FACING_BOARD,
        ortho_scale=board.width,
        clip_start=views.clip_start,
        clip_end=views.clip_end,
        collection=collection,
    )
    for view_name, sprite in views.sprites.items():
        new_orthographic_camera(
            _SPRITE_CAMERA_PREFIX + view_name.upper(),
            location=(sprite.x, views.camera_y, sprite.z),
            rotation_radians=_FACING_BOARD,
            ortho_scale=sprite.ortho_scale,
            clip_start=views.clip_start,
            clip_end=views.clip_end,
            collection=collection,
        )
    return board_camera
