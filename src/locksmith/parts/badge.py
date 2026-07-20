from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import (
    add_placed_cone,
    assign_untagged_faces,
    mesh_object_from,
    new_bmesh,
)
from locksmith.constants import QUARTER_TURN
from locksmith.schema.models.anatomy.badge.badge import BadgeAnatomy


def build_badge(
    *,
    anatomy: BadgeAnatomy,
    ring_material: Material,
    inlay_material: Material,
    collection: Collection,
) -> Object:
    """Master rosette: a tapered metal ring holding a proud enamel disc."""
    mesh_builder = new_bmesh()

    add_placed_cone(
        mesh_builder,
        segments=anatomy.ring.segments,
        base_radius=anatomy.ring.base_radius,
        top_radius=anatomy.ring.face_radius,
        depth=anatomy.ring.depth,
        axis="X",
        radians=QUARTER_TURN,
        offset=(0.0, anatomy.ring.y, 0.0),
    )
    assign_untagged_faces(mesh_builder, material_index=0)

    add_placed_cone(
        mesh_builder,
        segments=anatomy.inlay.segments,
        base_radius=anatomy.inlay.radius,
        top_radius=anatomy.inlay.radius,
        depth=anatomy.inlay.depth,
        axis="X",
        radians=QUARTER_TURN,
        offset=(0.0, anatomy.inlay.y, 0.0),
    )
    assign_untagged_faces(mesh_builder, material_index=1)

    return mesh_object_from(
        "badge_master",
        mesh_builder,
        collection=collection,
        materials=[ring_material, inlay_material],
    )
