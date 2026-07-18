from pathlib import Path

import bpy
from bpy.types import Scene


def blender_version() -> str:
    return str(bpy.app.version_string)


def active_scene() -> Scene:
    """Return the scene the current context operates on.

    Raises:
        RuntimeError: when the context carries no scene.
    """
    scene = bpy.context.scene
    if scene is None:
        raise RuntimeError("no scene in the current context")

    return scene


def reset_to_empty_factory_state() -> None:
    """Start the Blender session from an empty file.

    Building on an empty file gives the build full ownership of every
    datablock in the result; the factory startup scene would contribute its
    default cube, camera, and light.
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)


def save_blend(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(path))


def render_still(scene: Scene, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
