from bpy.types import Collection, Material, MaterialSlot, Object
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


def override_slot_material(instance: Object, *, slot: int, material: Material) -> None:
    """Give one object its own material while its siblings keep the mesh's.

    Material slots resolve through the shared mesh by default; relinking the
    slot to the object scopes the override to this instance.
    """
    material_slot: MaterialSlot = instance.material_slots[slot]
    material_slot.link = "OBJECT"
    material_slot.material = material
