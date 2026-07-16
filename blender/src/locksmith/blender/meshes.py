from typing import List, Literal, Sequence, cast

import bmesh
import bpy
from bmesh.types import BMEdge, BMesh, BMVert
from bpy.types import Collection, Material, Object
from mathutils import Matrix

from locksmith.types import Vec3

Axis = Literal["X", "Y", "Z"]

# bmesh.ops calls return loosely typed geometry dictionaries; the casts below
# own that boundary so builders work with concrete element lists.


def new_bmesh() -> BMesh:
    return bmesh.new()


def mesh_object_from(
    name: str,
    mesh_builder: BMesh,
    *,
    collection: Collection,
    materials: Sequence[Material],
) -> Object:
    """Bake a bmesh into a linked mesh object, freeing the builder."""
    mesh = bpy.data.meshes.new(name)
    mesh_builder.to_mesh(mesh)
    mesh_builder.free()
    for material in materials:
        mesh.materials.append(material)
    mesh_object = bpy.data.objects.new(name, mesh)
    collection.objects.link(mesh_object)
    return mesh_object


def box_vertices(mesh_builder: BMesh, *, size: Vec3, center: Vec3) -> List[BMVert]:
    created = bmesh.ops.create_cube(mesh_builder, size=1.0)
    vertices = cast(List[BMVert], created["verts"])
    bmesh.ops.scale(mesh_builder, vec=size, verts=vertices)
    bmesh.ops.translate(mesh_builder, vec=center, verts=vertices)
    return vertices


def cube_vertices(mesh_builder: BMesh) -> List[BMVert]:
    """Unit cube at the origin, meant to be scaled and placed by the caller."""
    created = bmesh.ops.create_cube(mesh_builder, size=1.0)
    return cast(List[BMVert], created["verts"])


def cone_vertices(
    mesh_builder: BMesh,
    *,
    segments: int,
    base_radius: float,
    top_radius: float,
    depth: float,
) -> List[BMVert]:
    """Capped cone centered on the origin along +z; equal radii yield a cylinder."""
    created = bmesh.ops.create_cone(
        mesh_builder,
        cap_ends=True,
        segments=segments,
        radius1=base_radius,
        radius2=top_radius,
        depth=depth,
    )
    return cast(List[BMVert], created["verts"])


def uv_sphere_vertices(
    mesh_builder: BMesh,
    *,
    segments: int,
    rings: int,
    radius: float,
) -> List[BMVert]:
    created = bmesh.ops.create_uvsphere(
        mesh_builder,
        u_segments=segments,
        v_segments=rings,
        radius=radius,
    )
    return cast(List[BMVert], created["verts"])


def scale_vertices(mesh_builder: BMesh, vertices: Sequence[BMVert], *, factors: Vec3) -> None:
    bmesh.ops.scale(mesh_builder, vec=factors, verts=list(vertices))


def translate_vertices(mesh_builder: BMesh, vertices: Sequence[BMVert], *, offset: Vec3) -> None:
    bmesh.ops.translate(mesh_builder, vec=offset, verts=list(vertices))


def rotate_vertices(mesh_builder: BMesh, vertices: Sequence[BMVert], *, axis: Axis, radians: float) -> None:
    """Spin vertices around the origin; rotate before translating into place."""
    matrix = Matrix.Rotation(radians, 3, axis)
    bmesh.ops.rotate(mesh_builder, cent=(0.0, 0.0, 0.0), matrix=matrix, verts=list(vertices))


def all_edges(mesh_builder: BMesh) -> List[BMEdge]:
    return list(mesh_builder.edges)


def edges_of_vertices(vertices: Sequence[BMVert]) -> List[BMEdge]:
    return list({edge for vertex in vertices for edge in vertex.link_edges})


def bevel_edges(
    mesh_builder: BMesh,
    edges: Sequence[BMEdge],
    *,
    offset: float,
    segments: int,
    profile: float,
) -> None:
    bmesh.ops.bevel(
        mesh_builder,
        geom=list(edges),
        offset=offset,
        offset_type="OFFSET",
        segments=segments,
        profile=profile,
        affect="EDGES",
        clamp_overlap=True,
    )


def subdivide_all_edges(mesh_builder: BMesh, *, cuts: int) -> None:
    bmesh.ops.subdivide_edges(mesh_builder, edges=all_edges(mesh_builder), cuts=cuts, use_grid_fill=True)


def assign_untagged_faces(mesh_builder: BMesh, *, material_index: int) -> None:
    """Give every face added since the last call this material slot.

    Face tags start cleared on creation, so tagging after each primitive
    partitions one mesh into per-part material regions.
    """
    for face in mesh_builder.faces:
        if not face.tag:
            face.material_index = material_index
            face.tag = True
