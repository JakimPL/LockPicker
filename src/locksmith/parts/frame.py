from typing import Tuple

from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import box_vertices, mesh_object_from, new_bmesh, subdivide_all_edges
from locksmith.blender.modifiers import apply_boolean_difference
from locksmith.board import BoardGeometry
from locksmith.schema.models.anatomy.plate import PlateAnatomy


def plate_span(*, board: BoardGeometry, anatomy: PlateAnatomy) -> Tuple[float, float]:
    """Horizontal extent of the plate: the slot columns plus a bezel each side."""
    left = board.column_center_x(0) - board.column_width / 2 - anatomy.bezel_left
    right = board.column_center_x(board.config.columns - 1) + board.column_width / 2 + anatomy.bezel_right
    return left, right


def build_frame(
    *,
    board: BoardGeometry,
    anatomy: PlateAnatomy,
    material: Material,
    collection: Collection,
) -> Object:
    """Housing plate with one slot cut per column; pins slide inside the slots.

    The plate is subdivided before the booleans so pointiness-driven shading
    stays local to the cut rims, and the cutters overshoot the plate so the
    booleans leave no coplanar faces. The chamber cut sinks everything
    between the shear lines into the depth fade: the shell face stays proud
    only on the first-height-unit bands, so each column reads as a pocket in
    the shell and the middle reads as the open raceway, running through both
    bezels — the mechanism continues past either edge of the case.
    """
    mesh_builder = new_bmesh()
    left, right = plate_span(board=board, anatomy=anatomy)
    width = right - left
    height = board.height + anatomy.margin
    depth = anatomy.back_y - anatomy.face_y
    box_vertices(
        mesh_builder, size=(width, depth, height), center=((left + right) / 2, anatomy.face_y + depth / 2, 0.0)
    )
    subdivide_all_edges(mesh_builder, cuts=anatomy.subdivision_cuts)
    plate = mesh_object_from("frame_plate", mesh_builder, collection=collection, materials=[material])

    cutter_builder = new_bmesh()
    for position in range(board.config.columns):
        box_vertices(
            cutter_builder,
            size=(
                board.column_width + anatomy.slot_clearance,
                depth + anatomy.cutter_depth_margin,
                height + anatomy.cutter_height_margin,
            ),
            center=(board.column_center_x(position), anatomy.face_y + depth / 2, 0.0),
        )
    cutter = mesh_object_from("frame_slots_cut", cutter_builder, collection=collection, materials=[])
    apply_boolean_difference(plate, name="slots", cutter=cutter)

    overshoot = anatomy.cutter_depth_margin / 2
    chamber_left = left - overshoot
    chamber_right = right + overshoot
    chamber_top = board.tip_z(upper=True, height=1.0)
    chamber_builder = new_bmesh()
    box_vertices(
        chamber_builder,
        size=(
            chamber_right - chamber_left,
            anatomy.chamber_depth + overshoot,
            2 * chamber_top,
        ),
        center=(
            (chamber_left + chamber_right) / 2,
            anatomy.face_y - overshoot + (anatomy.chamber_depth + overshoot) / 2,
            0.0,
        ),
    )
    chamber = mesh_object_from("frame_chamber_cut", chamber_builder, collection=collection, materials=[])
    apply_boolean_difference(plate, name="chamber", cutter=chamber)
    return plate


def build_sprite_stage(
    *,
    board: BoardGeometry,
    anatomy: PlateAnatomy,
    material: Material,
    collection: Collection,
) -> Object:
    """Bandless stand-in plate the translating sprites bake against.

    The real plate changes along the board height — proud shell bands, the
    chamber recess, the shell-band glow — so a sprite baked beside it picks
    up shading tied to one bake position and carries it to every runtime
    position. The stage is the chamber continued forever: its whole face
    sits at the chamber floor depth with the same slot windows, so every
    point of an eleven-unit pin bakes inside identical surroundings. It
    stays hidden except during the sprite passes.
    """
    mesh_builder = new_bmesh()
    left, right = plate_span(board=board, anatomy=anatomy)
    height = board.height + anatomy.margin
    face_y = anatomy.face_y + anatomy.chamber_depth
    depth = anatomy.back_y - face_y
    box_vertices(mesh_builder, size=(right - left, depth, height), center=((left + right) / 2, face_y + depth / 2, 0.0))
    stage = mesh_object_from("sprite_stage", mesh_builder, collection=collection, materials=[material])

    cutter_builder = new_bmesh()
    for position in range(board.config.columns):
        box_vertices(
            cutter_builder,
            size=(
                board.column_width + anatomy.slot_clearance,
                depth + anatomy.cutter_depth_margin,
                height + anatomy.cutter_height_margin,
            ),
            center=(board.column_center_x(position), face_y + depth / 2, 0.0),
        )
    cutter = mesh_object_from("sprite_stage_slots_cut", cutter_builder, collection=collection, materials=[])
    apply_boolean_difference(stage, name="slots", cutter=cutter)
    stage.hide_render = True
    return stage
