from typing import Tuple

from bpy.types import Collection, Material, MaterialSlot, Mesh, Object
from mathutils import Vector

from locksmith.types import Vec3


def linked_copy(prototype: Object, name: str, *, location: Vec3, collection: Collection) -> Object:
    """Place a render-enabled copy of a prototype; both objects share one mesh."""
    instance = prototype.copy()
    instance.name = name
    instance.location = Vector(location)
    instance.hide_render = False
    collection.objects.link(instance)
    return instance


def local_bounds(instance: Object) -> Tuple[Vec3, Vec3]:
    """Axis-aligned bounds of the object's mesh in its own local frame.

    Reading the raw mesh vertices keeps the result independent of the
    depsgraph, which only guarantees `bound_box` after an evaluation pass.

    Raises:
        TypeError: when the object carries no mesh.
        ValueError: when the mesh holds no vertices.
    """
    mesh = instance.data
    if not isinstance(mesh, Mesh):
        raise TypeError(f"object {instance.name!r} carries no mesh")
    coordinates = [vertex.co for vertex in mesh.vertices]  # type: ignore[attr-defined]  # stub hides iteration
    if not coordinates:
        raise ValueError(f"mesh of {instance.name!r} holds no vertices")
    minimum = (
        min(point.x for point in coordinates),
        min(point.y for point in coordinates),
        min(point.z for point in coordinates),
    )
    maximum = (
        max(point.x for point in coordinates),
        max(point.y for point in coordinates),
        max(point.z for point in coordinates),
    )
    return minimum, maximum


def set_camera_ray_visibility(instance: Object, *, visible: bool) -> None:
    """Toggle whether camera rays see the object while all other rays still do.

    Shadow passes hide the caster from the camera this way, so only its cast
    shadow reaches the film.
    """
    instance.visible_camera = visible


def override_slot_material(instance: Object, *, slot: int, material: Material) -> None:
    """Give one object its own material while its siblings keep the mesh's.

    Material slots resolve through the shared mesh by default; relinking the
    slot to the object scopes the override to this instance.
    """
    material_slot: MaterialSlot = instance.material_slots[slot]
    material_slot.link = "OBJECT"
    material_slot.material = material
