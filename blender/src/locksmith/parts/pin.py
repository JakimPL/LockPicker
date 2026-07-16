from typing import Final, Sequence

from bmesh.types import BMEdge, BMesh
from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import (
    all_edges,
    bevel_edges,
    box_vertices,
    edges_of_vertices,
    mesh_object_from,
    new_bmesh,
)
from locksmith.board import BoardGeometry
from locksmith.config.models.anatomy.bevel import EdgeBevel
from locksmith.config.models.anatomy.pin.pin import PinAnatomy

_LENGTH_TOLERANCE: Final[float] = 1e-3
_TIP_TOLERANCE: Final[float] = 1e-4
_FACE_TOLERANCE: Final[float] = 0.01


def build_pin(
    name: str,
    *,
    upper: bool,
    board: BoardGeometry,
    anatomy: PinAnatomy,
    material: Material,
    collection: Collection,
) -> Object:
    """Full-height pin with its origin at the free tip, extending away from the board.

    The mesh spans the whole max height; runtime blits anchor the tip and let
    screen clipping crop the length hidden inside the housing. Upper and
    lower pins are modeled separately because mirroring a render would flip
    the key light.
    """
    mesh_builder = new_bmesh()
    direction = 1.0 if upper else -1.0
    width = board.column_width - anatomy.width_margin
    length = board.config.max_height
    box_vertices(
        mesh_builder,
        size=(width, anatomy.depth, length),
        center=(0.0, anatomy.depth / 2, direction * length / 2),
    )

    long_edges = [
        edge
        for edge in all_edges(mesh_builder)
        if abs(edge.verts[0].co.z - edge.verts[1].co.z) > length - _LENGTH_TOLERANCE
    ]
    front_edges = [edge for edge in long_edges if all(vertex.co.y < _FACE_TOLERANCE for vertex in edge.verts)]
    back_edges = [
        edge for edge in long_edges if all(vertex.co.y > anatomy.depth - _FACE_TOLERANCE for vertex in edge.verts)
    ]
    _bevel(mesh_builder, front_edges, anatomy.shoulder_bevel)
    _bevel(mesh_builder, back_edges, anatomy.back_bevel)

    tip_edges = [
        edge for edge in all_edges(mesh_builder) if all(abs(vertex.co.z) < _TIP_TOLERANCE for vertex in edge.verts)
    ]
    _bevel(mesh_builder, tip_edges, anatomy.tip_bevel)

    collar = anatomy.collar
    collar_vertices = box_vertices(
        mesh_builder,
        size=(width + collar.width_margin, anatomy.depth + collar.depth_margin, collar.height),
        center=(0.0, anatomy.depth / 2, direction * collar.tip_distance),
    )
    _bevel(mesh_builder, edges_of_vertices(collar_vertices), collar.bevel)

    return mesh_object_from(name, mesh_builder, collection=collection, materials=[material])


def _bevel(mesh_builder: BMesh, edges: Sequence[BMEdge], bevel: EdgeBevel) -> None:
    bevel_edges(mesh_builder, edges, offset=bevel.offset, segments=bevel.segments, profile=bevel.profile)
