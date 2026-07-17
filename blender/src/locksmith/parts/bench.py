import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from bmesh.types import BMesh
from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import assign_untagged_faces, box_vertices, mesh_object_from, new_bmesh
from locksmith.board import BoardGeometry
from locksmith.config.models.anatomy.bench import BenchAnatomy

Span = Tuple[float, float]


@dataclass(frozen=True)
class PlankSpan:
    """One vertical run every plank fills, with its own horizontal limits.

    `inner_limit` clamps the plank boxes on the seam side — band runs tuck
    under the flange while the middle run stops at its edge — `mouth` leaves
    the keyway slot open where a plank crosses it, and `face_y` overrides
    the panel face for a run carved deeper into the bench.
    """

    bottom: float
    top: float
    inner_limit: float
    mouth: Optional[Span] = None
    face_y: Optional[float] = None
    material_index: int = 0


def build_bench(
    *,
    board: BoardGeometry,
    anatomy: BenchAnatomy,
    inner_left: float,
    inner_right: float,
    flange_clearance: float,
    mouth: Span,
    material: Material,
    carved_material: Material,
    collection: Collection,
) -> Object:
    """Wooden plank panels between the case seams and the board edges.

    The planks sit recessed behind the case faces so the metal keeps reading
    as the frontmost layer, and each panel marches outward from its seam so
    truncated planks land past the visible board. Both panels run between
    the shear lines too, carved down to the raceway channel that passes
    through the whole case — open at the keyway `mouth` on the left, plain
    on the right — with each carved run stopping `flange_clearance` short
    of its seam while the proud band runs tuck under the flange itself. The
    carved runs keep the plank grain but a deeper stain: the sun hits the
    recessed floor at the same angle as the proud faces, so depth alone
    would not darken it.
    """
    mesh_builder = new_bmesh()
    band_inner = board.tip_z(upper=True, height=1.0)
    band_outer = board.height / 2 + anatomy.margin / 2
    left_inner = inner_left + anatomy.overlap
    _panel_planks(
        mesh_builder,
        inner=left_inner,
        outer=-board.width / 2 - anatomy.overshoot,
        anatomy=anatomy,
        spans=(
            PlankSpan(band_inner, band_outer, left_inner),
            PlankSpan(-band_outer, -band_inner, left_inner),
            PlankSpan(
                -band_inner,
                band_inner,
                inner_left - flange_clearance,
                mouth=mouth,
                face_y=anatomy.carve_face_y,
                material_index=1,
            ),
        ),
    )
    right_inner = inner_right - anatomy.overlap
    _panel_planks(
        mesh_builder,
        inner=right_inner,
        outer=board.width / 2 + anatomy.overshoot,
        anatomy=anatomy,
        spans=(
            PlankSpan(band_inner, band_outer, right_inner),
            PlankSpan(-band_outer, -band_inner, right_inner),
            PlankSpan(
                -band_inner,
                band_inner,
                inner_right + flange_clearance,
                face_y=anatomy.carve_face_y,
                material_index=1,
            ),
        ),
    )
    return mesh_object_from("bench_planks", mesh_builder, collection=collection, materials=[material, carved_material])


def _panel_planks(
    mesh_builder: BMesh,
    *,
    inner: float,
    outer: float,
    anatomy: BenchAnatomy,
    spans: Sequence[PlankSpan],
) -> None:
    """Fill one panel with planks from its seam toward the board edge."""
    direction = 1.0 if outer > inner else -1.0
    pitch = anatomy.plank_width + anatomy.gap
    count = math.ceil(abs(outer - inner) / pitch)
    for index in range(count):
        near = inner + direction * index * pitch
        far = near + direction * anatomy.plank_width
        far = min(far, outer) if direction > 0 else max(far, outer)
        low, high = min(near, far), max(near, far)
        jitter = anatomy.depth_jitter[index % len(anatomy.depth_jitter)]
        back = anatomy.face_y + anatomy.depth
        for span in spans:
            face = (anatomy.face_y if span.face_y is None else span.face_y) + jitter
            if direction > 0:
                clamped = (max(low, span.inner_limit), high)
            else:
                clamped = (low, min(high, span.inner_limit))
            for segment_low, segment_high in _without_mouth(clamped, span.mouth):
                if segment_high - segment_low < anatomy.gap:
                    continue

                box_vertices(
                    mesh_builder,
                    size=(segment_high - segment_low, back - face, span.top - span.bottom),
                    center=(
                        (segment_low + segment_high) / 2,
                        (face + back) / 2,
                        (span.bottom + span.top) / 2,
                    ),
                )
                assign_untagged_faces(mesh_builder, material_index=span.material_index)


def _without_mouth(segment: Span, mouth: Optional[Span]) -> List[Span]:
    low, high = segment
    if high <= low:
        return []
    if mouth is None or mouth[1] <= low or mouth[0] >= high:
        return [segment]
    return [(low, min(mouth[0], high)), (max(mouth[1], low), high)]
