from bpy.types import Collection, Object

from locksmith.blender.cycles import mark_shadow_catcher
from locksmith.blender.meshes import box_vertices, mesh_object_from, new_bmesh
from locksmith.board import BoardGeometry
from locksmith.config.models.anatomy.shadow_catcher import ShadowCatcherAnatomy


def build_shadow_catcher(
    *,
    board: BoardGeometry,
    anatomy: ShadowCatcherAnatomy,
    collection: Collection,
) -> Object:
    """Shadow-only plane just in front of the back wall for the separate shadow sprites.

    It stays out of ordinary renders; the batch pipeline enables it alone to
    capture each pin's translation-invariant cast shadow.
    """
    mesh_builder = new_bmesh()
    box_vertices(
        mesh_builder,
        size=(board.width + anatomy.margin, anatomy.thickness, board.height + anatomy.margin),
        center=(0.0, anatomy.y, 0.0),
    )
    catcher = mesh_object_from("shadowcatcher", mesh_builder, collection=collection, materials=[])
    mark_shadow_catcher(catcher)
    catcher.hide_render = True
    return catcher
