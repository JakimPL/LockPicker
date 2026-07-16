import math
from typing import Final

from bpy.types import Collection, Object

from locksmith.blender.cameras import new_orthographic_camera
from locksmith.board import BoardGeometry
from locksmith.config.models.views.views import ViewsConfig
from locksmith.types import Vec3

_BOARD_CAMERA_NAME: Final[str] = "CAM_BOARD"
FACING_BOARD: Final[Vec3] = (math.pi / 2, 0.0, 0.0)


def build_board_camera(*, views: ViewsConfig, board: BoardGeometry, collection: Collection) -> Object:
    """Orthographic camera filling the frame with the board, looking straight down +y.

    Orthographic projection is a firm requirement: sprites translate across
    the board at runtime and only a perspective-free view keeps them valid at
    every position.
    """
    return new_orthographic_camera(
        _BOARD_CAMERA_NAME,
        location=(0.0, views.camera_y, 0.0),
        rotation_radians=FACING_BOARD,
        ortho_scale=board.width,
        clip_start=views.clip_start,
        clip_end=views.clip_end,
        collection=collection,
    )
