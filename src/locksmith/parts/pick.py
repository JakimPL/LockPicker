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
    uv_sphere_vertices,
)
from locksmith.board import BoardGeometry
from locksmith.schema.models.anatomy.pick.pick import PickAnatomy
from locksmith.types import PickShape

_QUARTER_TURN: Final[float] = math.pi / 2  # TODO: repeated constant definition
_EIGHTH_TURN: Final[float] = math.pi / 4


# TODO: refactor
def build_pick(
    name: str,
    *,
    shape: PickShape,
    board: BoardGeometry,
    anatomy: PickAnatomy,
    shaft_material: Material,
    ferrule_material: Material,
    grip_material: Material,
    collection: Collection,
) -> Object:
    """Pick tool along the x axis with its tip at the origin.

    The tip silhouette is the pick's identity, so it stays a clean diamond or
    circle from the camera; shaft, ferrule, and grip trail off screen to the
    left.
    """
    mesh_builder = new_bmesh()

    shaft_vertices = cone_vertices(
        mesh_builder,
        segments=anatomy.shaft.segments,
        base_radius=anatomy.shaft.radius,
        top_radius=anatomy.shaft.radius,
        depth=anatomy.shaft.length,
    )
    rotate_vertices(mesh_builder, shaft_vertices, axis="Y", radians=_QUARTER_TURN)
    translate_vertices(
        mesh_builder,
        shaft_vertices,
        offset=(anatomy.shaft.center_x, 0.0, 0.0),
    )
    assign_untagged_faces(mesh_builder, material_index=0)

    match shape:
        case PickShape.DIAMOND:
            tip_vertices = cube_vertices(mesh_builder)
            scale_vertices(
                mesh_builder,
                tip_vertices,
                factors=(
                    anatomy.diamond_tip.width,
                    anatomy.diamond_tip.depth,
                    anatomy.diamond_tip.height,
                ),
            )
            rotate_vertices(mesh_builder, tip_vertices, axis="Y", radians=_EIGHTH_TURN)
        case PickShape.CIRCLE:
            tip_vertices = uv_sphere_vertices(
                mesh_builder,
                segments=anatomy.circle_tip.segments,
                rings=anatomy.circle_tip.rings,
                radius=board.units(anatomy.circle_tip.radius_pixels),
            )
            scale_vertices(mesh_builder, tip_vertices, factors=(1.0, anatomy.circle_tip.depth_scale, 1.0))
    assign_untagged_faces(mesh_builder, material_index=0)

    ferrule_vertices = cone_vertices(
        mesh_builder,
        segments=anatomy.ferrule.segments,
        base_radius=anatomy.ferrule.radius,
        top_radius=anatomy.ferrule.radius,
        depth=anatomy.ferrule.length,
    )
    rotate_vertices(mesh_builder, ferrule_vertices, axis="Y", radians=_QUARTER_TURN)
    translate_vertices(mesh_builder, ferrule_vertices, offset=(anatomy.ferrule.center_x, 0.0, 0.0))
    assign_untagged_faces(mesh_builder, material_index=1)

    grip_vertices = cone_vertices(
        mesh_builder,
        segments=anatomy.grip.segments,
        base_radius=anatomy.grip.radius,
        top_radius=anatomy.grip.radius,
        depth=anatomy.grip.length,
    )
    rotate_vertices(mesh_builder, grip_vertices, axis="Y", radians=_QUARTER_TURN)
    translate_vertices(mesh_builder, grip_vertices, offset=(anatomy.grip.center_x, 0.0, 0.0))
    assign_untagged_faces(mesh_builder, material_index=2)

    return mesh_object_from(
        name,
        mesh_builder,
        collection=collection,
        materials=[shaft_material, ferrule_material, grip_material],
    )
