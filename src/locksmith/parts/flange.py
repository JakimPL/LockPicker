import math
from typing import Final, Tuple

from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import (
    assign_untagged_faces,
    box_vertices,
    cone_vertices,
    cube_vertices,
    mesh_object_from,
    new_bmesh,
    rotate_vertices,
    scale_vertices,
    translate_vertices,
)
from locksmith.board import BoardGeometry
from locksmith.schema.models.anatomy.flange.flange import FlangeAnatomy

_QUARTER_TURN: Final[float] = math.pi / 2  # TODO: repeating constant definitions, worth defining in constants


# TODO: refactor
def build_flanges(
    *,
    board: BoardGeometry,
    anatomy: FlangeAnatomy,
    seam_xs: Tuple[float, float],
    carved: Tuple[bool, bool],
    strip_material: Material,
    head_material: Material,
    slot_material: Material,
    collection: Collection,
) -> Object:
    """Angle-iron seam strips with fasteners, covering both wood/case joints.

    Fasteners march symmetrically from the board center so they stay inside
    the visible height while the strip itself overshoots it. A carved seam
    keeps its strip and fasteners only outside the shear lines, so nothing
    crosses the open mouth.
    """
    mesh_builder = new_bmesh()
    width = board.units(anatomy.width_pixels)
    band_inner = board.tip_z(upper=True, height=1.0)
    band_outer = board.height / 2 + anatomy.margin / 2
    for seam_x, seam_carved in zip(seam_xs, carved):
        spans = ((band_inner, band_outer), (-band_outer, -band_inner)) if seam_carved else ((-band_outer, band_outer),)
        for bottom, top in spans:
            box_vertices(
                mesh_builder,
                size=(width, anatomy.depth, top - bottom),
                center=(seam_x, anatomy.face_y + anatomy.depth / 2, (bottom + top) / 2),
            )

    assign_untagged_faces(mesh_builder, material_index=0)

    steps = int(board.height / 2 // anatomy.spacing_z)
    placements = [
        (seam_x, step * anatomy.spacing_z)
        for seam_x, seam_carved in zip(seam_xs, carved)
        for step in range(-steps, steps + 1)
        if not (seam_carved and abs(step * anatomy.spacing_z) < band_inner + anatomy.head.base_radius)
    ]

    for index, (fastener_x, fastener_z) in enumerate(placements):
        head_vertices = cone_vertices(
            mesh_builder,
            segments=anatomy.head.segments,
            base_radius=anatomy.head.base_radius,
            top_radius=anatomy.head.face_radius,
            depth=anatomy.head.depth,
        )
        rotate_vertices(mesh_builder, head_vertices, axis="X", radians=_QUARTER_TURN)
        translate_vertices(
            mesh_builder,
            head_vertices,
            offset=(fastener_x, anatomy.head.y, fastener_z),
        )
        assign_untagged_faces(mesh_builder, material_index=1)

        slot_vertices = cube_vertices(mesh_builder)
        scale_vertices(
            mesh_builder,
            slot_vertices,
            factors=(anatomy.slot.length, anatomy.slot.depth, anatomy.slot.height),
        )
        angle = anatomy.slot_angles[index % len(anatomy.slot_angles)]
        rotate_vertices(mesh_builder, slot_vertices, axis="Y", radians=angle)
        translate_vertices(
            mesh_builder,
            slot_vertices,
            offset=(fastener_x, anatomy.slot.y, fastener_z),
        )
        assign_untagged_faces(mesh_builder, material_index=2)

    return mesh_object_from(
        "case_flanges",
        mesh_builder,
        collection=collection,
        materials=[strip_material, head_material, slot_material],
    )
