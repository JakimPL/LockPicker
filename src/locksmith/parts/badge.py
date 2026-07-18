import math
from typing import Final

from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import (
    assign_untagged_faces,
    cone_vertices,
    mesh_object_from,
    new_bmesh,
    rotate_vertices,
    translate_vertices,
)
from locksmith.schema.models.anatomy.badge.badge import BadgeAnatomy

_QUARTER_TURN: Final[float] = math.pi / 2


def build_badge(
    *,
    anatomy: BadgeAnatomy,
    ring_material: Material,
    inlay_material: Material,
    collection: Collection,
) -> Object:
    """Master rosette: a tapered metal ring holding a proud enamel disc."""
    mesh_builder = new_bmesh()

    ring_vertices = cone_vertices(
        mesh_builder,
        segments=anatomy.ring.segments,
        base_radius=anatomy.ring.base_radius,
        top_radius=anatomy.ring.face_radius,
        depth=anatomy.ring.depth,
    )
    rotate_vertices(mesh_builder, ring_vertices, axis="X", radians=_QUARTER_TURN)
    translate_vertices(mesh_builder, ring_vertices, offset=(0.0, anatomy.ring.y, 0.0))
    assign_untagged_faces(mesh_builder, material_index=0)

    inlay_vertices = cone_vertices(
        mesh_builder,
        segments=anatomy.inlay.segments,
        base_radius=anatomy.inlay.radius,
        top_radius=anatomy.inlay.radius,
        depth=anatomy.inlay.depth,
    )
    rotate_vertices(mesh_builder, inlay_vertices, axis="X", radians=_QUARTER_TURN)
    translate_vertices(mesh_builder, inlay_vertices, offset=(0.0, anatomy.inlay.y, 0.0))
    assign_untagged_faces(mesh_builder, material_index=1)

    return mesh_object_from(
        "badge_master", mesh_builder, collection=collection, materials=[ring_material, inlay_material]
    )
