from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import box_vertices, mesh_object_from, new_bmesh, subdivide_all_edges
from locksmith.blender.modifiers import apply_boolean_difference
from locksmith.board import BoardGeometry
from locksmith.config.models.anatomy.plate import PlateAnatomy


def build_frame(
    *,
    board: BoardGeometry,
    anatomy: PlateAnatomy,
    material: Material,
    collection: Collection,
) -> Object:
    """Housing plate with one slot cut per column; pins slide inside the slots.

    The plate is subdivided before the boolean so pointiness-driven shading
    stays local to the slot rims, and the cutter overshoots the plate on
    every axis so the boolean leaves no coplanar faces.
    """
    mesh_builder = new_bmesh()
    width = board.width + anatomy.margin
    height = board.height + anatomy.margin
    depth = anatomy.back_y - anatomy.face_y
    box_vertices(mesh_builder, size=(width, depth, height), center=(0.0, anatomy.face_y + depth / 2, 0.0))
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
    return plate
