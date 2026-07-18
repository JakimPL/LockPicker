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
    """Radius of one bore, shrunk just below the pitch so plate lands survive.

    Sized a hair under the column half-width so the bore aligns with the hole
    drilled through the faceplate above it: the pin drops into the bore, and
    neighbouring bores no longer overlap, leaving a strip of plate — the land
    — between every column. The outermost rims still hide behind the plate's
    end jambs.
    """
    return board.column_width / 2 - plate.land_inset


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

    Each column is a full-height concave half-cylinder channel behind its
    faceplate hole: the pin sinks into the bore that fits it and the scene
    suns shade the curve, instead of a painted gradient on a flat panel. The
    channel sits behind the plate, so the plate's drilled rim frames it and
    the deep wall behind stays dark.
    """
    mesh_builder = new_bmesh()
    box_vertices(
        mesh_builder,
        size=(board.width + anatomy.margin, anatomy.depth, board.height + anatomy.margin),
        center=(0.0, anatomy.center_y, 0.0),
    )
    assign_untagged_faces(mesh_builder, material_index=0)

    radius = trough_radius(board=board, plate=plate)
    span = board.height + anatomy.margin
    for position in range(board.config.columns):
        trough_vertices = half_pipe_vertices(
            mesh_builder,
            radius=radius,
            span=span,
            segments=anatomy.pocket_segments,
        )
        translate_vertices(
            mesh_builder,
            trough_vertices,
            offset=(board.column_center_x(position), anatomy.pocket_y, 0.0),
        )
    assign_untagged_faces(mesh_builder, material_index=1)

    return mesh_object_from("bg_wall", mesh_builder, collection=collection, materials=[wall_material, pocket_material])
