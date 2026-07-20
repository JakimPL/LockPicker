from pathlib import Path

from bpy.types import Object, Scene

from locksmith.assets.batch.constants import _CAMERA_PREFIX
from locksmith.assets.framing import SpriteFraming, sprite_framing
from locksmith.assets.manifest.sprite import SpriteAsset
from locksmith.assets.png import require_png_size
from locksmith.blender.cameras import new_orthographic_camera
from locksmith.blender.objects import local_bounds
from locksmith.blender.scene_state import rendered
from locksmith.blender.session import render_still
from locksmith.builder import WorkshopScene
from locksmith.rendering.cameras import FACING_BOARD
from locksmith.schema.models.scene import SceneConfig
from locksmith.types import PixelPair


def _render_sprite(
    workshop: WorkshopScene,
    *,
    prototype: Object,
    framing: SpriteFraming,
    config: SceneConfig,
    path: Path,
) -> None:
    """Render one transparent pass framed pixel-true on the parked prototype."""
    pixels_per_unit = workshop.board.config.pixels_per_unit
    offset_x, offset_z = framing.center_offset(pixels_per_unit=pixels_per_unit)
    camera = new_orthographic_camera(
        _CAMERA_PREFIX + path.stem.upper(),
        location=(
            prototype.location.x + offset_x,
            config.views.camera_y,
            prototype.location.z + offset_z,
        ),
        rotation_radians=FACING_BOARD,
        ortho_scale=framing.ortho_width(pixels_per_unit=pixels_per_unit),
        clip_start=config.views.clip_start,
        clip_end=config.views.clip_end,
        collection=workshop.collections.rig,
    )
    scene = workshop.scene
    scene.camera = camera
    _set_canvas(scene, size=framing.size, image_scale=config.assets.image_scale)
    scene.render.film_transparent = True
    _render_file(
        scene,
        path,
        expected=_scaled(framing.size, config.assets.image_scale),
    )


def _render_prototype_sprite(
    workshop: WorkshopScene,
    *,
    prototype: Object,
    framing: SpriteFraming,
    config: SceneConfig,
    path: Path,
) -> SpriteAsset:
    with rendered(prototype):
        _render_sprite(workshop, prototype=prototype, framing=framing, config=config, path=path)
    return SpriteAsset(
        image=path.name,
        size=framing.size,
        tip_anchor=framing.anchor,
    )


def _framed(prototype: Object, *, workshop: WorkshopScene, config: SceneConfig) -> SpriteFraming:
    return sprite_framing(
        local_bounds(prototype),
        pixels_per_unit=workshop.board.config.pixels_per_unit,
        padding_pixels=config.assets.padding_pixels,
    )


def _slot_x(workshop: WorkshopScene) -> float:
    """Center of the middle column; sprite passes render inside a real slot.

    Slots repeat identically per column and run uniformly past the visible
    board, so the baked surroundings stay valid wherever the sprite
    translates at runtime.
    """
    return workshop.board.column_center_x(workshop.board.config.columns // 2)


def _scaled(size: PixelPair, image_scale: int) -> PixelPair:
    return size[0] * image_scale, size[1] * image_scale


def _set_canvas(scene: Scene, *, size: PixelPair, image_scale: int) -> None:
    scene.render.resolution_x = size[0] * image_scale
    scene.render.resolution_y = size[1] * image_scale


def _render_file(scene: Scene, path: Path, *, expected: PixelPair) -> None:
    render_still(scene, path)
    require_png_size(path, expected)
    print(f"rendered: {path.name} ({expected[0]}x{expected[1]})")
