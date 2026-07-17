from typing import Tuple

from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import assign_untagged_faces, box_vertices, mesh_object_from, new_bmesh
from locksmith.board import BoardGeometry
from locksmith.config.models.anatomy.keyway.keyway import KeywayAnatomy


def keyway_mouth_span(*, board: BoardGeometry, anatomy: KeywayAnatomy) -> Tuple[float, float]:
    """Horizontal extent of the slot opening in the bench panel."""
    half_width = board.units(anatomy.width_pixels) / 2
    center = board.x_at(anatomy.center_pixels)
    return center - half_width, center + half_width


def build_keyway(
    *,
    board: BoardGeometry,
    anatomy: KeywayAnatomy,
    bushing_material: Material,
    bed_material: Material,
    collection: Collection,
) -> Object:
    """Brass-lined tool slot behind the bench panel's mouth opening.

    The dark raceway bed floors the opening from behind while two proud
    vertical brass liners frame it in front of the wood — the wear plates
    every pick slides between. Both overshoot the opening and the shear
    lines so their ends hide behind the planks and the lip rails.
    """
    mesh_builder = new_bmesh()
    slot_left, slot_right = keyway_mouth_span(board=board, anatomy=anatomy)
    liner_width = board.units(anatomy.bushing.width_pixels)
    band_inner = board.tip_z(upper=True, height=1.0)
    liner_half_span = band_inner + anatomy.bushing.overshoot

    for liner_left in (slot_left - liner_width, slot_right):
        box_vertices(
            mesh_builder,
            size=(liner_width, anatomy.bushing.depth, 2 * liner_half_span),
            center=(liner_left + liner_width / 2, anatomy.bushing.face_y + anatomy.bushing.depth / 2, 0.0),
        )
    assign_untagged_faces(mesh_builder, material_index=0)

    bed_left = slot_left - liner_width - anatomy.overshoot
    bed_right = slot_right + liner_width + anatomy.overshoot
    bed_half_span = band_inner + anatomy.overshoot
    bed_depth = anatomy.back_y - anatomy.bed_face_y
    box_vertices(
        mesh_builder,
        size=(bed_right - bed_left, bed_depth, 2 * bed_half_span),
        center=((bed_left + bed_right) / 2, anatomy.bed_face_y + bed_depth / 2, 0.0),
    )
    assign_untagged_faces(mesh_builder, material_index=1)

    return mesh_object_from(
        "keyway_mouth",
        mesh_builder,
        collection=collection,
        materials=[bushing_material, bed_material],
    )
