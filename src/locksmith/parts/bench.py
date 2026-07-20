import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from bmesh.types import BMesh
from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import (
    assign_untagged_faces,
    crowned_box_vertices,
    mesh_object_from,
    new_bmesh,
)
from locksmith.board import BoardGeometry
from locksmith.schema.models.anatomy.bench import BenchAnatomy

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


@dataclass(frozen=True)
class _PlankRun:
    low: float
    high: float
    jitter: float


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
    for seam, outward, panel_mouth in ((inner_left, -1.0, mouth), (inner_right, 1.0, None)):
        panel_inner = seam - outward * anatomy.overlap
        _panel_planks(
            mesh_builder,
            inner=panel_inner,
            outer=outward * (board.width / 2 + anatomy.overshoot),
            anatomy=anatomy,
            spans=_panel_spans(
                seam=seam,
                outward=outward,
                panel_inner=panel_inner,
                band_inner=band_inner,
                band_outer=band_outer,
                flange_clearance=flange_clearance,
                anatomy=anatomy,
                mouth=panel_mouth,
            ),
        )
    return mesh_object_from(
        "bench_planks",
        mesh_builder,
        collection=collection,
        materials=[material, carved_material],
    )


def _panel_spans(
    *,
    seam: float,
    outward: float,
    panel_inner: float,
    band_inner: float,
    band_outer: float,
    flange_clearance: float,
    anatomy: BenchAnatomy,
    mouth: Optional[Span],
) -> Tuple[PlankSpan, ...]:
    return (
        PlankSpan(band_inner, band_outer, panel_inner),
        PlankSpan(-band_outer, -band_inner, panel_inner),
        PlankSpan(
            -band_inner,
            band_inner,
            seam + outward * flange_clearance,
            mouth=mouth,
            face_y=anatomy.carve_face_y,
            material_index=1,
        ),
    )


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
    for run in _plank_runs(inner=inner, outer=outer, direction=direction, anatomy=anatomy):
        for span in spans:
            _add_plank_segment(mesh_builder, run=run, span=span, direction=direction, anatomy=anatomy)


def _plank_runs(
    *,
    inner: float,
    outer: float,
    direction: float,
    anatomy: BenchAnatomy,
) -> List[_PlankRun]:
    pitch = anatomy.plank_width + anatomy.gap
    count = math.ceil(abs(outer - inner) / pitch)
    runs: List[_PlankRun] = []
    for index in range(count):
        near = inner + direction * index * pitch
        far = near + direction * anatomy.plank_width
        far = min(far, outer) if direction > 0 else max(far, outer)
        low, high = min(near, far), max(near, far)
        jitter = anatomy.depth_jitter[index % len(anatomy.depth_jitter)]
        runs.append(_PlankRun(low=low, high=high, jitter=jitter))

    return runs


def _add_plank_segment(
    mesh_builder: BMesh,
    *,
    run: _PlankRun,
    span: PlankSpan,
    direction: float,
    anatomy: BenchAnatomy,
) -> None:
    face = (anatomy.face_y if span.face_y is None else span.face_y) + run.jitter
    back = anatomy.face_y + anatomy.depth
    if direction > 0:
        clamped = (max(run.low, span.inner_limit), run.high)
    else:
        clamped = (run.low, min(run.high, span.inner_limit))

    for segment_low, segment_high in _without_mouth(clamped, span.mouth):
        if segment_high - segment_low < anatomy.gap:
            continue

        crowned_box_vertices(
            mesh_builder,
            size=(segment_high - segment_low, back - face, span.top - span.bottom),
            center=(
                (segment_low + segment_high) / 2,
                (face + back) / 2,
                (span.bottom + span.top) / 2,
            ),
            crown=anatomy.crown,
            segments=anatomy.crown_segments,
        )
        assign_untagged_faces(mesh_builder, material_index=span.material_index)


def _without_mouth(segment: Span, mouth: Optional[Span]) -> List[Span]:
    low, high = segment
    if high <= low:
        return []

    if mouth is None or mouth[1] <= low or mouth[0] >= high:
        return [segment]

    return [(low, min(mouth[0], high)), (max(mouth[1], low), high)]
