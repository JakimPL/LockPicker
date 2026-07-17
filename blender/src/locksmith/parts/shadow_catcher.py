from bpy.types import Collection, Object

from locksmith.blender.cycles import mark_shadow_catcher
from locksmith.blender.meshes import half_pipe_vertices, mesh_object_from, new_bmesh, translate_vertices
from locksmith.board import BoardGeometry
from locksmith.config.models.anatomy.background import BackgroundAnatomy
from locksmith.config.models.anatomy.plate import PlateAnatomy
from locksmith.config.models.anatomy.shadow_catcher import ShadowCatcherAnatomy
from locksmith.parts.background import trough_radius


def build_shadow_catcher(
    *,
    board: BoardGeometry,
    anatomy: ShadowCatcherAnatomy,
    plate: PlateAnatomy,
    background: BackgroundAnatomy,
    collection: Collection,
) -> Object:
    """Shadow-only replica of one bore trough for the separate shadow sprites.

    A pin's cast shadow lands inside its own bore, so the catcher copies the
    trough shape exactly: the baked shadow hugs the pin and bends with the
    curve instead of smearing across a distant flat wall. It sits at x = 0;
    the batch pipeline moves it under whichever prototype it captures. It
    stays out of ordinary renders.
    """
    mesh_builder = new_bmesh()
    trough_vertices = half_pipe_vertices(
        mesh_builder,
        radius=trough_radius(board=board, plate=plate),
        span=board.height + anatomy.margin,
        segments=background.pocket_segments,
    )
    translate_vertices(mesh_builder, trough_vertices, offset=(0.0, background.pocket_y, 0.0))
    catcher = mesh_object_from("shadowcatcher", mesh_builder, collection=collection, materials=[])
    mark_shadow_catcher(catcher)
    catcher.hide_render = True
    return catcher
