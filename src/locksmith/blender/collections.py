import bpy
from bpy.types import Collection, Scene


def new_child_collection(scene: Scene, name: str) -> Collection:
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    return collection
