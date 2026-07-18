from bpy.types import Collection, Object

from locksmith.blender.cycles import mark_shadow_catcher
from locksmith.blender.meshes import (
    cosine_flute_profile,
    extruded_profile_vertices,
    mesh_object_from,
    new_bmesh,
    translate_vertices,
)
from locksmith.board import BoardGeometry
from locksmith.parts.background import trough_radius
from locksmith.schema.models.anatomy.background import BackgroundAnatomy
from locksmith.schema.models.anatomy.plate import PlateAnatomy
from locksmith.schema.models.anatomy.shadow_catcher import ShadowCatcherAnatomy


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
    pitch = board.column_center_x(1) - board.column_center_x(0)
    profile = cosine_flute_profile(
        start_x=-pitch / 2.0,
        end_x=pitch / 2.0,
        phase_x=0.0,
        pitch=pitch,
        depth=trough_radius(board=board, plate=plate),
        steps=background.pocket_segments,
    )
    trough_vertices = extruded_profile_vertices(mesh_builder, profile=profile, span=board.height + anatomy.margin)
    translate_vertices(mesh_builder, trough_vertices, offset=(0.0, background.pocket_y, 0.0))
    catcher = mesh_object_from("shadowcatcher", mesh_builder, collection=collection, materials=[])
    mark_shadow_catcher(catcher)
    catcher.hide_render = True
    return catcher
