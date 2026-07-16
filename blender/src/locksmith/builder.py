from typing import Final

from bpy.types import Scene

from locksmith.blender.lights import new_sun_light
from locksmith.blender.session import active_scene, reset_to_empty_factory_state
from locksmith.board import BoardGeometry
from locksmith.colors import linear_rgb
from locksmith.config.models.scene import SceneConfig
from locksmith.lookdev import build_lookdev
from locksmith.parts.background import build_background
from locksmith.parts.frame import build_frame
from locksmith.parts.screws import build_screws
from locksmith.parts.shadow_catcher import build_shadow_catcher
from locksmith.rendering.cameras import build_cameras
from locksmith.rendering.settings import apply_render_settings
from locksmith.scene_collections import build_scene_collections
from locksmith.shading.library import make_material_library
from locksmith.staging import build_prototypes
from locksmith.world import build_world

_KEY_SUN_NAME: Final[str] = "sun_key"
_RIM_SUN_NAME: Final[str] = "sun_rim"


def build_scene(config: SceneConfig) -> Scene:
    """Build the whole workshop scene into a fresh Blender session."""
    reset_to_empty_factory_state()
    scene = active_scene()
    board = BoardGeometry(config.board)
    library = make_material_library(palette=config.palette, shading=config.shading)
    collections = build_scene_collections(scene)

    build_world(scene, palette=config.palette, config=config.world)
    build_background(
        board=board,
        anatomy=config.anatomy.background,
        material=library.bore,
        collection=collections.background,
    )
    build_frame(board=board, anatomy=config.anatomy.plate, material=library.plate, collection=collections.frame)
    build_screws(
        anatomy=config.anatomy.screws,
        head_material=library.rosette,
        slot_material=library.bore,
        collection=collections.frame,
    )
    prototypes = build_prototypes(
        board=board,
        anatomy=config.anatomy,
        library=library,
        staging=config.staging,
        collections=collections,
    )
    build_shadow_catcher(board=board, anatomy=config.anatomy.shadow_catcher, collection=collections.shadow_catcher)

    new_sun_light(
        _KEY_SUN_NAME,
        direction=config.lighting.key.direction,
        color=linear_rgb(config.palette.key),
        energy=config.lighting.key.energy,
        angle=config.lighting.key.angle,
        collection=collections.rig,
    )
    new_sun_light(
        _RIM_SUN_NAME,
        direction=config.lighting.rim.direction,
        color=linear_rgb(config.palette.rim),
        energy=config.lighting.rim.energy,
        angle=config.lighting.rim.angle,
        collection=collections.rig,
    )
    board_camera = build_cameras(views=config.views, board=board, collection=collections.rig)

    build_lookdev(
        config=config.lookdev,
        prototypes=prototypes,
        library=library,
        board=board,
        collection=collections.lookdev,
    )

    device_type = apply_render_settings(scene, config.render)
    print(f"cycles compute device: {device_type}")
    scene.camera = board_camera
    return scene
