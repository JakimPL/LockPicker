from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import (
    assign_untagged_faces,
    box_vertices,
    cosine_flute_profile,
    extruded_profile_vertices,
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
    """Back wall behind the mechanism, fluted into one bore per column.

    The column field is a single continuous surface of raised-cosine flutes:
    each column drops into its own concave hollow that the pin sinks into and
    the suns shade, and consecutive hollows meet at a smooth crest instead of
    a sharp rim over a dark gap — so the luminosity glides across every
    boundary. The fluted field sits in front of the deep wall, which the
    plate's drilled rims frame column by column.
    """
    mesh_builder = new_bmesh()
    box_vertices(
        mesh_builder,
        size=(board.width + anatomy.margin, anatomy.depth, board.height + anatomy.margin),
        center=(0.0, anatomy.center_y, 0.0),
    )
    assign_untagged_faces(mesh_builder, material_index=0)

    span = board.height + anatomy.margin
    first = board.column_center_x(0)
    pitch = board.column_center_x(1) - first
    profile = cosine_flute_profile(
        start_x=first - pitch / 2.0,
        end_x=board.column_center_x(board.config.columns - 1) + pitch / 2.0,
        phase_x=first,
        pitch=pitch,
        depth=trough_radius(board=board, plate=plate),
        steps=anatomy.pocket_segments * board.config.columns,
    )
    trough_vertices = extruded_profile_vertices(mesh_builder, profile=profile, span=span)
    translate_vertices(mesh_builder, trough_vertices, offset=(0.0, anatomy.pocket_y, 0.0))
    assign_untagged_faces(mesh_builder, material_index=1)

    return mesh_object_from("bg_wall", mesh_builder, collection=collection, materials=[wall_material, pocket_material])
