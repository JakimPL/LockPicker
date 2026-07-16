from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import box_vertices, mesh_object_from, new_bmesh
from locksmith.board import BoardGeometry
from locksmith.config.models.anatomy.background import BackgroundAnatomy


def build_background(
    *,
    board: BoardGeometry,
    anatomy: BackgroundAnatomy,
    material: Material,
    collection: Collection,
) -> Object:
    """Back wall behind the mechanism, deep enough that it stays out of focus and near-black."""
    mesh_builder = new_bmesh()
    box_vertices(
        mesh_builder,
        size=(board.width + anatomy.margin, anatomy.depth, board.height + anatomy.margin),
        center=(0.0, anatomy.center_y, 0.0),
    )
    return mesh_object_from("bg_wall", mesh_builder, collection=collection, materials=[material])
