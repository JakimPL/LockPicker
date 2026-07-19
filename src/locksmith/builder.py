from dataclasses import dataclass
from typing import Final

from bpy.types import Object, Scene

from locksmith.blender.lights import new_sun_light
from locksmith.blender.session import active_scene, reset_to_empty_factory_state
from locksmith.board import BoardGeometry
from locksmith.colors import linear_rgb
from locksmith.lookdev import build_lookdev
from locksmith.parts.background import build_background
from locksmith.parts.bench import build_bench
from locksmith.parts.flange import build_flanges
from locksmith.parts.frame import build_frame, build_sprite_stage, plate_span
from locksmith.parts.keyway import build_keyway, keyway_mouth_span
from locksmith.parts.lip import build_lip
from locksmith.parts.screws import build_screws
from locksmith.parts.shadow_catcher import build_shadow_catcher
from locksmith.rendering.cameras import build_board_camera
from locksmith.rendering.settings import AppliedRenderSettings, apply_render_settings
from locksmith.scene_collections import SceneCollections, build_scene_collections
from locksmith.schema.models.scene import SceneConfig
from locksmith.shading.library import MaterialLibrary, make_material_library
from locksmith.staging import Prototypes, build_prototypes
from locksmith.world import build_world

_KEY_SUN_NAME: Final[str] = "sun_key"
_RIM_SUN_NAME: Final[str] = "sun_rim"
_FILL_SUN_NAME: Final[str] = "sun_fill"


@dataclass(frozen=True)
class WorkshopScene:
    """The built scene plus the handles later stages steer.

    The batch pipeline toggles collections and prototypes per sprite pass,
    reframes cameras, and records the applied render settings as manifest
    provenance, so the builder hands all of that over explicitly.
    """

    scene: Scene
    board: BoardGeometry
    collections: SceneCollections
    prototypes: Prototypes
    library: MaterialLibrary
    background_wall: Object
    frame_plate: Object
    sprite_stage: Object
    bench: Object
    keyway: Object
    flanges: Object
    lip_upper: Object
    lip_lower: Object
    screws: Object
    shadow_catcher: Object
    key_sun: Object
    rim_sun: Object
    fill_sun: Object
    board_camera: Object
    render_settings: AppliedRenderSettings


def build_scene(config: SceneConfig) -> WorkshopScene:
    """Build the whole workshop scene into a fresh Blender session."""
    reset_to_empty_factory_state()
    scene = active_scene()
    board = BoardGeometry(config.board)
    library = make_material_library(
        palette=config.palette,
        shading=config.shading,
        plate_half_height=board.height / 2,
    )
    collections = build_scene_collections(scene)

    build_world(scene, palette=config.palette, config=config.world)
    background_wall = build_background(
        board=board,
        anatomy=config.anatomy.background,
        plate=config.anatomy.plate,
        wall_material=library.bore,
        pocket_material=library.pocket,
        collection=collections.background,
    )
    frame_plate = build_frame(
        board=board,
        anatomy=config.anatomy.plate,
        material=library.plate,
        collection=collections.frame,
    )
    sprite_stage = build_sprite_stage(
        board=board,
        anatomy=config.anatomy.plate,
        material=library.plate_stage,
        collection=collections.background,
    )
    plate_left, plate_right = plate_span(
        board=board,
        anatomy=config.anatomy.plate,
    )
    bench = build_bench(
        board=board,
        anatomy=config.anatomy.bench,
        inner_left=plate_left,
        inner_right=plate_right,
        flange_clearance=board.units(config.anatomy.flange.width_pixels) / 2,
        mouth=keyway_mouth_span(board=board, anatomy=config.anatomy.keyway),
        material=library.wood,
        carved_material=library.wood_carved,
        collection=collections.frame,
    )
    keyway = build_keyway(
        board=board,
        anatomy=config.anatomy.keyway,
        bushing_material=library.lip,
        bed_material=library.raceway,
        collection=collections.frame,
    )
    flanges = build_flanges(
        board=board,
        anatomy=config.anatomy.flange,
        seam_xs=(plate_left, plate_right),
        carved=(True, True),
        strip_material=library.rosette,
        head_material=library.rosette,
        slot_material=library.bore,
        collection=collections.frame,
    )
    lip_upper = build_lip(
        "lip_upper",
        board=board,
        anatomy=config.anatomy.lip,
        plate=config.anatomy.plate,
        line_z=board.tip_z(upper=True, height=1.0),
        material=library.lip,
        collection=collections.lip_upper,
    )
    lip_lower = build_lip(
        "lip_lower",
        board=board,
        anatomy=config.anatomy.lip,
        plate=config.anatomy.plate,
        line_z=board.tip_z(upper=False, height=1.0),
        material=library.lip,
        collection=collections.lip_lower,
    )
    screws = build_screws(
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
    shadow_catcher = build_shadow_catcher(
        board=board,
        anatomy=config.anatomy.shadow_catcher,
        plate=config.anatomy.plate,
        background=config.anatomy.background,
        collection=collections.shadow_catcher,
    )

    key_sun = new_sun_light(
        _KEY_SUN_NAME,
        direction=config.lighting.key.direction,
        color=linear_rgb(config.palette.key),
        energy=config.lighting.key.energy,
        angle=config.lighting.key.angle,
        collection=collections.rig,
    )
    rim_sun = new_sun_light(
        _RIM_SUN_NAME,
        direction=config.lighting.rim.direction,
        color=linear_rgb(config.palette.rim),
        energy=config.lighting.rim.energy,
        angle=config.lighting.rim.angle,
        collection=collections.rig,
    )
    fill_sun = new_sun_light(
        _FILL_SUN_NAME,
        direction=config.lighting.fill.direction,
        color=linear_rgb(config.palette.rim),
        energy=config.lighting.fill.energy,
        angle=config.lighting.fill.angle,
        collection=collections.rig,
    )
    board_camera = build_board_camera(
        views=config.views,
        board=board,
        collection=collections.rig,
    )

    build_lookdev(
        config=config.lookdev,
        badge_tip_offset_pixels=config.assets.badge_tip_offset_pixels,
        prototypes=prototypes,
        library=library,
        board=board,
        collection=collections.lookdev,
    )

    render_settings = apply_render_settings(scene, config.render)
    print(f"cycles compute device: {render_settings.device_type}")
    scene.camera = board_camera
    return WorkshopScene(
        scene=scene,
        board=board,
        collections=collections,
        prototypes=prototypes,
        library=library,
        background_wall=background_wall,
        frame_plate=frame_plate,
        sprite_stage=sprite_stage,
        bench=bench,
        keyway=keyway,
        flanges=flanges,
        lip_upper=lip_upper,
        lip_lower=lip_lower,
        screws=screws,
        shadow_catcher=shadow_catcher,
        key_sun=key_sun,
        rim_sun=rim_sun,
        fill_sun=fill_sun,
        board_camera=board_camera,
        render_settings=render_settings,
    )
