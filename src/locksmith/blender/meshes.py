import math
from typing import List, Literal, Sequence, Tuple, cast

import bmesh
import bpy
from bmesh.types import BMEdge, BMesh, BMVert
from bpy.types import Collection, Material, Object
from mathutils import Matrix

from locksmith.types import Vec3

Axis = Literal["X", "Y", "Z"]


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


def box_vertices(
    mesh_builder: BMesh,
    *,
    size: Vec3,
    center: Vec3,
) -> List[BMVert]:
    created = bmesh.ops.create_cube(mesh_builder, size=1.0)
    vertices = cast(List[BMVert], created["verts"])
    bmesh.ops.scale(mesh_builder, vec=size, verts=vertices)
    bmesh.ops.translate(mesh_builder, vec=center, verts=vertices)
    return vertices


def cube_vertices(mesh_builder: BMesh) -> List[BMVert]:
    """Unit cube at the origin, meant to be scaled and placed by the caller."""
    created = bmesh.ops.create_cube(mesh_builder, size=1.0)
    return cast(List[BMVert], created["verts"])


# TODO: refactor
def crowned_box_vertices(
    mesh_builder: BMesh,
    *,
    size: Vec3,
    center: Vec3,
    crown: float,
    segments: int,
) -> List[BMVert]:
    """Box whose front (-y) face bulges toward the camera in a shallow arc.

    The front face is sampled across x into `segments` strips and pulled
    toward the camera by up to `crown` at the middle, tapering to the flat
    edges, and smooth-shaded so a distant sun renders a real luminance
    gradient across the plank instead of one flat tone. The other five faces
    stay square, keeping each plank a closed solid whose seams read as
    grooves between neighbours.
    """
    half = (size[0] / 2.0, size[1] / 2.0, size[2] / 2.0)
    low_x, high_x = center[0] - half[0], center[0] + half[0]
    front_y, back_y = center[1] - half[1], center[1] + half[1]
    low_z, high_z = center[2] - half[2], center[2] + half[2]
    top_front: List[BMVert] = []
    bottom_front: List[BMVert] = []
    for index in range(segments + 1):
        fraction = index / segments
        x = low_x + (high_x - low_x) * fraction
        y = front_y - crown * math.sin(math.pi * fraction)
        top_front.append(mesh_builder.verts.new((x, y, high_z)))
        bottom_front.append(mesh_builder.verts.new((x, y, low_z)))

    back = [
        mesh_builder.verts.new((corner_x, back_y, corner_z))
        for corner_z in (high_z, low_z)
        for corner_x in (low_x, high_x)
    ]

    for index in range(segments):
        face = mesh_builder.faces.new(
            (top_front[index], top_front[index + 1], bottom_front[index + 1], bottom_front[index])
        )
        face.smooth = True
        if face.normal.y > 0.0:
            face.normal_flip()

    mesh_builder.faces.new((back[1], back[0], back[2], back[3]))
    mesh_builder.faces.new((top_front[0], back[0], back[2], bottom_front[0]))
    mesh_builder.faces.new((top_front[-1], bottom_front[-1], back[3], back[1]))
    mesh_builder.faces.new(tuple(top_front) + (back[1], back[0]))
    mesh_builder.faces.new(tuple(reversed(bottom_front)) + (back[2], back[3]))
    return top_front + bottom_front + back


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


def add_placed_cone(
    mesh_builder: BMesh,
    *,
    segments: int,
    base_radius: float,
    top_radius: float,
    depth: float,
    axis: Axis,
    radians: float,
    offset: Vec3,
) -> List[BMVert]:
    vertices = cone_vertices(
        mesh_builder,
        segments=segments,
        base_radius=base_radius,
        top_radius=top_radius,
        depth=depth,
    )
    rotate_vertices(mesh_builder, vertices, axis=axis, radians=radians)
    translate_vertices(mesh_builder, vertices, offset=offset)
    return vertices


def cosine_flute_profile(
    *,
    start_x: float,
    end_x: float,
    phase_x: float,
    pitch: float,
    depth: float,
    steps: int,
) -> List[Tuple[float, float]]:
    """Cross-section of raised-cosine flutes: hollows on the pitch, crests between.

    Each column sits in a concave hollow `depth` deep at `phase_x` plus whole
    pitches; midway between two hollows the curve tops out at a smooth crest
    at y=0 with a flat tangent, so consecutive flutes meet without a seam or a
    sharp rim. Sampled across `[start_x, end_x]` so the whole field is one
    continuous surface, the luminosity glides from bore to boundary with no
    hard step to a deep gap.
    """
    points: List[Tuple[float, float]] = []
    for index in range(steps + 1):
        x = start_x + (end_x - start_x) * index / steps
        y = depth * 0.5 * (1.0 + math.cos(2.0 * math.pi * (x - phase_x) / pitch))
        points.append((x, y))

    return points


def extruded_profile_vertices(
    mesh_builder: BMesh,
    *,
    profile: Sequence[Tuple[float, float]],
    span: float,
) -> List[BMVert]:
    """Sweep a 2D x-y profile along z into a smooth-shaded surface facing -y.

    The profile is a bore seen in section; extruding it the full span gives
    the trough its length, and the faces are wound so their normals face the
    opening (the camera) and smooth-shade across the curve.
    """
    half_z = span / 2.0
    top = [mesh_builder.verts.new((x, y, half_z)) for x, y in profile]
    bottom = [mesh_builder.verts.new((x, y, -half_z)) for x, y in profile]
    for index in range(len(profile) - 1):
        face = mesh_builder.faces.new(
            (
                top[index],
                bottom[index],
                bottom[index + 1],
                top[index + 1],
            )
        )
        face.smooth = True
        if face.normal.y > 0.0:
            face.normal_flip()

    return top + bottom


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


def scale_vertices(
    mesh_builder: BMesh,
    vertices: Sequence[BMVert],
    *,
    factors: Vec3,
) -> None:
    bmesh.ops.scale(mesh_builder, vec=factors, verts=list(vertices))


def translate_vertices(
    mesh_builder: BMesh,
    vertices: Sequence[BMVert],
    *,
    offset: Vec3,
) -> None:
    bmesh.ops.translate(mesh_builder, vec=offset, verts=list(vertices))


def rotate_vertices(
    mesh_builder: BMesh,
    vertices: Sequence[BMVert],
    *,
    axis: Axis,
    radians: float,
) -> None:
    """Spin vertices around the origin; rotate before translating into place."""
    matrix = Matrix.Rotation(radians, 3, axis)
    bmesh.ops.rotate(
        mesh_builder,
        cent=(0.0, 0.0, 0.0),
        matrix=matrix,
        verts=list(vertices),
    )


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


def subdivide_edges(
    mesh_builder: BMesh,
    edges: Sequence[BMEdge],
    *,
    cuts: int,
) -> None:
    bmesh.ops.subdivide_edges(
        mesh_builder,
        edges=list(edges),
        cuts=cuts,
        use_grid_fill=True,
    )


def subdivide_all_edges(mesh_builder: BMesh, *, cuts: int) -> None:
    subdivide_edges(mesh_builder, all_edges(mesh_builder), cuts=cuts)


def assign_untagged_faces(mesh_builder: BMesh, *, material_index: int) -> None:
    """Give every face added since the last call this material slot.

    Face tags start cleared on creation, so tagging after each primitive
    partitions one mesh into per-part material regions.
    """
    for face in mesh_builder.faces:
        if not face.tag:
            face.material_index = material_index
            face.tag = True
