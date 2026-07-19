from dataclasses import dataclass
from typing import Tuple

from bmesh.types import BMesh
from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import (
    box_vertices,
    cube_vertices,
    mesh_object_from,
    new_bmesh,
    subdivide_all_edges,
)
from locksmith.blender.modifiers import apply_boolean_difference
from locksmith.board import BoardGeometry
from locksmith.parts.slots import cut_column_slots
from locksmith.schema.models.anatomy.plate import PlateAnatomy


def plate_span(
    *,
    board: BoardGeometry,
    anatomy: PlateAnatomy,
) -> Tuple[float, float]:
    """Horizontal extent of the plate: the slot columns plus a bezel each side."""
    left = board.column_center_x(0) - board.column_width / 2 - anatomy.bezel_left
    right = board.column_center_x(board.config.columns - 1) + board.column_width / 2 + anatomy.bezel_right
    return left, right


def slot_width(*, board: BoardGeometry, anatomy: PlateAnatomy) -> float:
    """Width of one bore hole through the plate, matched to the bore diameter.

    Sized a hair under the column pitch so a strip of plate — the land —
    survives between neighbouring holes; the pin drops through with a sliver
    of clearance and the plate rim frames it, so each column reads as a hole
    drilled through solid metal.
    """
    return board.column_width - 2 * anatomy.land_inset


@dataclass(frozen=True)
class _CountersinkProfile:
    front_half: float
    back_half: float
    front_y: float
    back_y: float
    half_z: float


def _carve_countersink_prism(
    mesh_builder: BMesh,
    *,
    center_x: float,
    profile: _CountersinkProfile,
) -> None:
    for vertex in cube_vertices(mesh_builder):
        front = vertex.co.y < 0.0
        vertex.co.x = center_x + (1.0 if vertex.co.x > 0.0 else -1.0) * (
            profile.front_half if front else profile.back_half
        )
        vertex.co.y = profile.front_y if front else profile.back_y
        vertex.co.z = (1.0 if vertex.co.z > 0.0 else -1.0) * profile.half_z


def _countersink_cutter(
    *,
    board: BoardGeometry,
    anatomy: PlateAnatomy,
    hole_width: float,
    height: float,
) -> BMesh:
    """One tapered prism per column that carves the front of each slot to a chamfer.

    Each prism is a cube distorted into a wedge: its front face (toward the
    camera) spans `countersink_width` wider than the bore on each side, its
    back face narrows to the bore over `countersink_depth`, and the top and
    bottom stay vertical so only the column-facing rims — the lands between
    columns — get the machined shoulder. A front overshoot clears the plate
    face so the boolean leaves no coplanar sliver.
    """
    overshoot = anatomy.cutter_depth_margin / 2
    profile = _CountersinkProfile(
        front_half=hole_width / 2 + anatomy.countersink_width,
        back_half=hole_width / 2,
        front_y=anatomy.face_y - overshoot,
        back_y=anatomy.face_y + anatomy.countersink_depth,
        half_z=(height + anatomy.cutter_height_margin) / 2,
    )
    builder = new_bmesh()
    for position in range(board.config.columns):
        _carve_countersink_prism(builder, center_x=board.column_center_x(position), profile=profile)

    return builder


def _build_plate_blank(
    *,
    board: BoardGeometry,
    anatomy: PlateAnatomy,
    material: Material,
    collection: Collection,
) -> Object:
    mesh_builder = new_bmesh()
    left, right = plate_span(board=board, anatomy=anatomy)
    width = right - left
    height = board.height + anatomy.margin
    depth = anatomy.back_y - anatomy.face_y
    box_vertices(
        mesh_builder,
        size=(width, depth, height),
        center=((left + right) / 2, anatomy.face_y + depth / 2, 0.0),
    )
    subdivide_all_edges(mesh_builder, cuts=anatomy.subdivision_cuts)
    return mesh_object_from(
        "frame_plate",
        mesh_builder,
        collection=collection,
        materials=[material],
    )


def _cut_countersink(
    plate: Object,
    *,
    board: BoardGeometry,
    anatomy: PlateAnatomy,
    hole_width: float,
    height: float,
    collection: Collection,
) -> None:
    countersink = mesh_object_from(
        "frame_countersink_cut",
        _countersink_cutter(board=board, anatomy=anatomy, hole_width=hole_width, height=height),
        collection=collection,
        materials=[],
    )
    apply_boolean_difference(plate, name="countersink", cutter=countersink)


def _cut_chamber(
    plate: Object,
    *,
    board: BoardGeometry,
    anatomy: PlateAnatomy,
    collection: Collection,
) -> None:
    left, right = plate_span(board=board, anatomy=anatomy)
    overshoot = anatomy.cutter_depth_margin / 2
    chamber_left = left - overshoot
    chamber_right = right + overshoot
    chamber_top = board.tip_z(upper=True, height=1.0)
    chamber_builder = new_bmesh()
    box_vertices(
        chamber_builder,
        size=(
            chamber_right - chamber_left,
            anatomy.chamber_depth + overshoot,
            2 * chamber_top,
        ),
        center=(
            (chamber_left + chamber_right) / 2,
            anatomy.face_y - overshoot + (anatomy.chamber_depth + overshoot) / 2,
            0.0,
        ),
    )
    chamber = mesh_object_from(
        "frame_chamber_cut",
        chamber_builder,
        collection=collection,
        materials=[],
    )
    apply_boolean_difference(plate, name="chamber", cutter=chamber)


def build_frame(
    *,
    board: BoardGeometry,
    anatomy: PlateAnatomy,
    material: Material,
    collection: Collection,
) -> Object:
    """Housing faceplate with one bore hole drilled per column; pins sink through them.

    The plate is subdivided before the booleans so pointiness-driven shading
    stays local to the cut rims — a bright glint on each hole rim — and the
    cutters overshoot the plate so the booleans leave no coplanar faces. One
    hole per column leaves solid lands between them, so the field reads as
    bores through a faceplate rather than an open window. The chamber cut
    sinks everything between the shear lines into the depth fade, running
    through both bezels — the mechanism continues past either edge of the case.
    """
    plate = _build_plate_blank(board=board, anatomy=anatomy, material=material, collection=collection)
    hole_width = slot_width(board=board, anatomy=anatomy)
    depth = anatomy.back_y - anatomy.face_y
    height = board.height + anatomy.margin
    cut_column_slots(
        plate,
        board=board,
        anatomy=anatomy,
        name="frame_slots_cut",
        hole_width=hole_width,
        depth=depth,
        height=height,
        center_y=anatomy.face_y + depth / 2,
        collection=collection,
    )
    _cut_countersink(plate, board=board, anatomy=anatomy, hole_width=hole_width, height=height, collection=collection)
    _cut_chamber(plate, board=board, anatomy=anatomy, collection=collection)
    return plate


def _build_stage_blank(
    *,
    board: BoardGeometry,
    anatomy: PlateAnatomy,
    material: Material,
    collection: Collection,
) -> Object:
    mesh_builder = new_bmesh()
    left, right = plate_span(board=board, anatomy=anatomy)
    height = board.height + anatomy.margin
    face_y = anatomy.face_y + anatomy.chamber_depth
    depth = anatomy.back_y - face_y
    box_vertices(
        mesh_builder,
        size=(right - left, depth, height),
        center=((left + right) / 2, face_y + depth / 2, 0.0),
    )
    return mesh_object_from(
        "sprite_stage",
        mesh_builder,
        collection=collection,
        materials=[material],
    )


def build_sprite_stage(
    *,
    board: BoardGeometry,
    anatomy: PlateAnatomy,
    material: Material,
    collection: Collection,
) -> Object:
    """Bandless stand-in plate the translating sprites bake against.

    The real plate changes along the board height — proud shell bands, the
    chamber recess, the shell-band glow — so a sprite baked beside it picks
    up shading tied to one bake position and carries it to every runtime
    position. The stage is the chamber continued forever: its whole face
    sits at the chamber floor depth with the same slot windows, so every
    point of an eleven-unit pin bakes inside identical surroundings. It
    stays hidden except during the sprite passes.
    """
    stage = _build_stage_blank(board=board, anatomy=anatomy, material=material, collection=collection)
    height = board.height + anatomy.margin
    face_y = anatomy.face_y + anatomy.chamber_depth
    depth = anatomy.back_y - face_y
    cut_column_slots(
        stage,
        board=board,
        anatomy=anatomy,
        name="sprite_stage_slots_cut",
        hole_width=slot_width(board=board, anatomy=anatomy),
        depth=depth,
        height=height,
        center_y=face_y + depth / 2,
        collection=collection,
    )
    stage.hide_render = True
    return stage
