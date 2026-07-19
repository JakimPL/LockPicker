from typing import Final

from bpy.types import Collection, Material, Object
from mathutils import Vector

from locksmith.blender.meshes import (
    all_edges,
    bevel_edges,
    box_vertices,
    mesh_object_from,
    new_bmesh,
)
from locksmith.board import BoardGeometry
from locksmith.parts.slots import cut_column_slots
from locksmith.schema.models.anatomy.lip import LipAnatomy
from locksmith.schema.models.anatomy.plate import PlateAnatomy

_LENGTH_TOLERANCE: Final[float] = 1e-3


def _build_rail_blank(
    name: str,
    *,
    board: BoardGeometry,
    anatomy: LipAnatomy,
    material: Material,
    collection: Collection,
) -> Object:
    mesh_builder = new_bmesh()
    thickness = board.units(anatomy.thickness_pixels)
    left = -board.width / 2 - thickness
    right = board.width / 2 + thickness
    width = right - left
    box_vertices(
        mesh_builder,
        size=(width, anatomy.depth, thickness),
        center=((left + right) / 2, anatomy.face_y + anatomy.depth / 2, 0.0),
    )
    long_edges = [
        edge
        for edge in all_edges(mesh_builder)
        if abs(edge.verts[0].co.x - edge.verts[1].co.x) > width - _LENGTH_TOLERANCE
    ]
    bevel_edges(
        mesh_builder,
        long_edges,
        offset=anatomy.bevel.offset,
        segments=anatomy.bevel.segments,
        profile=anatomy.bevel.profile,
    )
    return mesh_object_from(
        name,
        mesh_builder,
        collection=collection,
        materials=[material],
    )


def build_lip(
    name: str,
    *,
    board: BoardGeometry,
    anatomy: LipAnatomy,
    plate: PlateAnatomy,
    line_z: float,
    material: Material,
    collection: Collection,
) -> Object:
    """Slotted shear-rail crossing the whole case, z-centered on its origin.

    The origin lands exactly on the shear line, so the sprite framing anchor
    publishes the line row. One slot punched per column lets the pins pass
    behind the rail — the apertures are the tumbler slots on the line —
    while the beveled long edges catch the key sun as the polished-wear
    highlight. The rail runs past both screen edges, bounding the carved
    raceway along the whole case. The slot boolean stays live, so the
    cutter must ride along to `line_z` with the rail.
    """
    thickness = board.units(anatomy.thickness_pixels)
    lip = _build_rail_blank(name, board=board, anatomy=anatomy, material=material, collection=collection)
    cutter = cut_column_slots(
        lip,
        board=board,
        anatomy=plate,
        name=f"{name}_slots_cut",
        hole_width=board.column_width + plate.slot_clearance,
        depth=anatomy.depth,
        height=thickness,
        center_y=anatomy.face_y + anatomy.depth / 2,
        collection=collection,
    )
    lip.location = Vector((0.0, 0.0, line_z))
    cutter.location = Vector((0.0, 0.0, line_z))
    return lip
