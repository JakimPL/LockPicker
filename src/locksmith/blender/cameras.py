import bpy
from bpy.types import Collection, Object
from mathutils import Euler, Vector

from locksmith.types import Vec3


def new_orthographic_camera(
    name: str,
    *,
    location: Vec3,
    rotation_radians: Vec3,
    ortho_scale: float,
    clip_start: float,
    clip_end: float,
    collection: Collection,
) -> Object:
    camera_data = bpy.data.cameras.new(name)
    camera_data.type = "ORTHO"
    camera_data.sensor_fit = "HORIZONTAL"
    camera_data.ortho_scale = ortho_scale
    camera_data.clip_start = clip_start
    camera_data.clip_end = clip_end
    camera = bpy.data.objects.new(name, camera_data)
    camera.location = Vector(location)
    camera.rotation_euler = Euler(rotation_radians)
    collection.objects.link(camera)
    return camera
