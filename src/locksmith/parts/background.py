from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import (
    assign_untagged_faces,
    box_vertices,
    half_pipe_vertices,
    mesh_object_from,
    new_bmesh,
    translate_vertices,
)
from locksmith.board import BoardGeometry
from locksmith.schema.models.anatomy.background import BackgroundAnatomy
from locksmith.schema.models.anatomy.plate import PlateAnatomy


def trough_radius(*, board: BoardGeometry, plate: PlateAnatomy) -> float:
    """Radius of one bore trough, sized so its rims hide behind the window jambs."""
    return (board.column_width + 2 * plate.slot_clearance) / 2


def build_background(
    *,
    board: BoardGeometry,
    anatomy: BackgroundAnatomy,
    plate: PlateAnatomy,
    wall_material: Material,
    pocket_material: Material,
    collection: Collection,
) -> Object:
    """Back wall behind the mechanism, with a real bore trough per column.

    Each column carries a full-height concave half-cylinder channel sized to
    the slot window, so the cylindrical pin visibly rides in the groove that
    fits it: the scene suns shade the curve and the window jambs cast real
    shadows into it, instead of a painted gradient on a flat panel. The
    trough overshoots the window by one slot clearance per side so its
    grazing rims hide behind the jambs.
    """
    mesh_builder = new_bmesh()
    box_vertices(
        mesh_builder,
        size=(board.width + anatomy.margin, anatomy.depth, board.height + anatomy.margin),
        center=(0.0, anatomy.center_y, 0.0),
    )
    assign_untagged_faces(mesh_builder, material_index=0)

    radius = trough_radius(board=board, plate=plate)
    for position in range(board.config.columns):
        trough_vertices = half_pipe_vertices(
            mesh_builder,
            radius=radius,
            span=board.height + anatomy.margin,
            segments=anatomy.pocket_segments,
        )
        translate_vertices(
            mesh_builder,
            trough_vertices,
            offset=(board.column_center_x(position), anatomy.pocket_y, 0.0),
        )
    assign_untagged_faces(mesh_builder, material_index=1)

    return mesh_object_from("bg_wall", mesh_builder, collection=collection, materials=[wall_material, pocket_material])
