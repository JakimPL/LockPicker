import math

from bmesh.types import BMesh
from bpy.types import Collection, Material, Object

from locksmith.blender.meshes import box_vertices, mesh_object_from, new_bmesh
from locksmith.board import BoardGeometry
from locksmith.config.models.anatomy.bench import BenchAnatomy
from locksmith.config.models.anatomy.plate import PlateAnatomy
from locksmith.parts.frame import plate_span


def build_bench(
    *,
    board: BoardGeometry,
    anatomy: BenchAnatomy,
    plate: PlateAnatomy,
    material: Material,
    collection: Collection,
) -> Object:
    """Wooden plank panels between the housing plate and the board edges.

    The planks sit recessed behind the plate face so the plate keeps reading
    as the frontmost metal layer, and each panel marches outward from the
    plate so truncated planks land past the visible board.
    """
    mesh_builder = new_bmesh()
    height = board.height + anatomy.margin
    plate_left, plate_right = plate_span(board=board, anatomy=plate)
    _panel_planks(
        mesh_builder,
        inner=plate_left + anatomy.overlap,
        outer=-board.width / 2 - anatomy.overshoot,
        anatomy=anatomy,
        height=height,
    )
    _panel_planks(
        mesh_builder,
        inner=plate_right - anatomy.overlap,
        outer=board.width / 2 + anatomy.overshoot,
        anatomy=anatomy,
        height=height,
    )
    return mesh_object_from("bench_planks", mesh_builder, collection=collection, materials=[material])


def _panel_planks(
    mesh_builder: BMesh,
    *,
    inner: float,
    outer: float,
    anatomy: BenchAnatomy,
    height: float,
) -> None:
    """Fill one panel with planks from its plate edge toward the board edge."""
    direction = 1.0 if outer > inner else -1.0
    pitch = anatomy.plank_width + anatomy.gap
    count = math.ceil(abs(outer - inner) / pitch)
    for index in range(count):
        near = inner + direction * index * pitch
        far = near + direction * anatomy.plank_width
        far = min(far, outer) if direction > 0 else max(far, outer)
        width = abs(far - near)
        if width < anatomy.gap:
            continue

        face = anatomy.face_y + anatomy.depth_jitter[index % len(anatomy.depth_jitter)]
        box_vertices(
            mesh_builder,
            size=(width, anatomy.depth, height),
            center=((near + far) / 2, face + anatomy.depth / 2, 0.0),
        )
