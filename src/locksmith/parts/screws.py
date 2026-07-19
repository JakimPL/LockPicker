import math
from typing import Final

from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import (
    assign_untagged_faces,
    cone_vertices,
    cube_vertices,
    mesh_object_from,
    new_bmesh,
    rotate_vertices,
    scale_vertices,
    translate_vertices,
)
from locksmith.schema.models.anatomy.screws.screws import ScrewsAnatomy

_QUARTER_TURN: Final[float] = math.pi / 2


def build_screws(
    *,
    anatomy: ScrewsAnatomy,
    head_material: Material,
    slot_material: Material,
    collection: Collection,
) -> Object:
    """All plate screws in one mesh: countersunk heads with darkened driver slots."""
    mesh_builder = new_bmesh()
    for placement in anatomy.placements:
        head_vertices = cone_vertices(
            mesh_builder,
            segments=anatomy.head.segments,
            base_radius=anatomy.head.base_radius,
            top_radius=anatomy.head.face_radius,
            depth=anatomy.head.depth,
        )
        rotate_vertices(mesh_builder, head_vertices, axis="X", radians=_QUARTER_TURN)
        translate_vertices(mesh_builder, head_vertices, offset=(placement.x, anatomy.head.y, placement.z))
        assign_untagged_faces(mesh_builder, material_index=0)

        slot_vertices = cube_vertices(mesh_builder)
        scale_vertices(
            mesh_builder,
            slot_vertices,
            factors=(anatomy.slot.length, anatomy.slot.depth, anatomy.slot.height),
        )
        rotate_vertices(mesh_builder, slot_vertices, axis="Y", radians=placement.slot_angle)
        translate_vertices(mesh_builder, slot_vertices, offset=(placement.x, anatomy.slot.y, placement.z))
        assign_untagged_faces(mesh_builder, material_index=1)

    return mesh_object_from(
        "frame_screws",
        mesh_builder,
        collection=collection,
        materials=[head_material, slot_material],
    )
