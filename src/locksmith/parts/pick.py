from typing import Protocol

from bmesh.types import BMesh
from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import (
    add_placed_cone,
    assign_untagged_faces,
    cube_vertices,
    mesh_object_from,
    new_bmesh,
    rotate_vertices,
    scale_vertices,
    uv_sphere_vertices,
)
from locksmith.board import BoardGeometry
from locksmith.constants import EIGHTH_TURN, QUARTER_TURN
from locksmith.schema.models.anatomy.pick.circle_tip import CircleTipAnatomy
from locksmith.schema.models.anatomy.pick.diamond_tip import DiamondTipAnatomy
from locksmith.schema.models.anatomy.pick.pick import PickAnatomy
from locksmith.types import PickShape


class CylindricalPart(Protocol):
    @property
    def segments(self) -> int: ...

    @property
    def radius(self) -> float: ...

    @property
    def length(self) -> float: ...

    @property
    def center_x(self) -> float: ...


def _add_cylinder_part(
    mesh_builder: BMesh,
    part: CylindricalPart,
    *,
    material_index: int,
) -> None:
    add_placed_cone(
        mesh_builder,
        segments=part.segments,
        base_radius=part.radius,
        top_radius=part.radius,
        depth=part.length,
        axis="Y",
        radians=QUARTER_TURN,
        offset=(part.center_x, 0.0, 0.0),
    )
    assign_untagged_faces(mesh_builder, material_index=material_index)


def _add_diamond_tip(mesh_builder: BMesh, *, anatomy: DiamondTipAnatomy) -> None:
    tip_vertices = cube_vertices(mesh_builder)
    scale_vertices(
        mesh_builder,
        tip_vertices,
        factors=(anatomy.width, anatomy.depth, anatomy.height),
    )
    rotate_vertices(mesh_builder, tip_vertices, axis="Y", radians=EIGHTH_TURN)


def _add_circle_tip(
    mesh_builder: BMesh,
    *,
    anatomy: CircleTipAnatomy,
    board: BoardGeometry,
) -> None:
    tip_vertices = uv_sphere_vertices(
        mesh_builder,
        segments=anatomy.segments,
        rings=anatomy.rings,
        radius=board.units(anatomy.radius_pixels),
    )
    scale_vertices(mesh_builder, tip_vertices, factors=(1.0, anatomy.depth_scale, 1.0))


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

    _add_cylinder_part(mesh_builder, anatomy.shaft, material_index=0)

    match shape:
        case PickShape.DIAMOND:
            _add_diamond_tip(mesh_builder, anatomy=anatomy.diamond_tip)
        case PickShape.CIRCLE:
            _add_circle_tip(mesh_builder, anatomy=anatomy.circle_tip, board=board)
    assign_untagged_faces(mesh_builder, material_index=0)

    _add_cylinder_part(mesh_builder, anatomy.ferrule, material_index=1)
    _add_cylinder_part(mesh_builder, anatomy.grip, material_index=2)

    return mesh_object_from(
        name,
        mesh_builder,
        collection=collection,
        materials=[shaft_material, ferrule_material, grip_material],
    )
