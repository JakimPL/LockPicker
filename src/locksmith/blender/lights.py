import bpy
from bpy.types import Collection, Object, SunLight
from mathutils import Color, Vector

from locksmith.types import RGBColor, Vec3


def new_sun_light(
    name: str,
    *,
    direction: Vec3,
    color: RGBColor,
    energy: float,
    angle: float,
    collection: Collection,
) -> Object:
    """Parallel-ray sun shining along `direction`; a wider angle softens its shadows."""
    light_data = bpy.data.lights.new(name, "SUN")
    if not isinstance(light_data, SunLight):
        raise TypeError(f"expected SunLight, Blender created {type(light_data).__name__}")

    light_data.color = Color(color)
    light_data.energy = energy
    light_data.angle = angle
    light = bpy.data.objects.new(name, light_data)
    light.rotation_mode = "QUATERNION"
    light.rotation_quaternion = Vector(direction).normalized().to_track_quat("-Z", "Y")
    collection.objects.link(light)
    return light
