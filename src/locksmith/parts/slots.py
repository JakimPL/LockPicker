from bpy.types import Collection, Object

from locksmith.blender.meshes import box_vertices, mesh_object_from, new_bmesh
from locksmith.blender.modifiers import apply_boolean_difference
from locksmith.board import BoardGeometry
from locksmith.schema.models.anatomy.plate import PlateAnatomy


def cut_column_slots(
    target: Object,
    *,
    board: BoardGeometry,
    anatomy: PlateAnatomy,
    name: str,
    hole_width: float,
    depth: float,
    height: float,
    center_y: float,
    collection: Collection,
) -> Object:
    cutter_builder = new_bmesh()
    for position in range(board.config.columns):
        box_vertices(
            cutter_builder,
            size=(
                hole_width,
                depth + anatomy.cutter_depth_margin,
                height + anatomy.cutter_height_margin,
            ),
            center=(board.column_center_x(position), center_y, 0.0),
        )

    cutter = mesh_object_from(name, cutter_builder, collection=collection, materials=[])
    apply_boolean_difference(target, name="slots", cutter=cutter)
    return cutter
