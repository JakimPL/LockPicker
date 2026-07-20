from pathlib import Path
from typing import Dict

from bpy.types import Object
from mathutils import Vector

from locksmith.assets.batch.constants import _PIN_FILENAME, _SHADOW_FILENAME
from locksmith.assets.batch.sprite import _render_sprite, _slot_x
from locksmith.assets.framing import Bounds, shadow_framing, sprite_framing
from locksmith.assets.manifest.sprite import SpriteAsset
from locksmith.assets.manifest.tumbler_orientation import TumblerOrientationAssets
from locksmith.blender.objects import local_bounds, override_slot_material
from locksmith.blender.scene_state import camera_ray_hidden, hidden, rendered, world_disabled
from locksmith.builder import WorkshopScene
from locksmith.parts.background import trough_radius
from locksmith.schema.models.scene import SceneConfig
from locksmith.types import Metal


def _render_tumbler_orientation(
    workshop: WorkshopScene,
    *,
    upper: bool,
    config: SceneConfig,
    directory: Path,
) -> TumblerOrientationAssets:
    """Render every metal variant of one pin orientation plus its shadow.

    All variants share one mesh and therefore one framing; only the material
    override changes between renders. The banded plate and the zoned trough
    make way for their stage stand-ins so every point of the shaft bakes
    inside the same chamber surroundings — a translating sprite must carry
    no shading tied to one bake height.
    """
    prototype = workshop.prototypes.tumbler_upper if upper else workshop.prototypes.tumbler_lower
    prototype.location = Vector((_slot_x(workshop), 0.0, config.assets.pin_bake_tip_z))
    bounds = local_bounds(prototype)
    framing = sprite_framing(
        bounds,
        pixels_per_unit=workshop.board.config.pixels_per_unit,
        padding_pixels=config.assets.padding_pixels,
    )
    orientation = "upper" if upper else "lower"
    images: Dict[Metal, str] = {}
    with hidden(workshop.frame_plate), rendered(workshop.sprite_stage, prototype):
        for metal in dict.fromkeys(config.assets.groups):
            override_slot_material(
                prototype,
                slot=0,
                material=workshop.library.tumblers[metal],
            )
            filename = _PIN_FILENAME.format(metal=metal.value, orientation=orientation)
            _render_sprite(
                workshop,
                prototype=prototype,
                framing=framing,
                config=config,
                path=directory / filename,
            )
            images[metal] = filename

    shadow = _render_shadow(
        workshop,
        prototype=prototype,
        bounds=bounds,
        config=config,
        path=directory / _SHADOW_FILENAME.format(orientation=orientation),
    )
    return TumblerOrientationAssets(
        images=images,
        size=framing.size,
        tip_anchor=framing.anchor,
        shadow=shadow,
    )


def _render_shadow(
    workshop: WorkshopScene,
    *,
    prototype: Object,
    bounds: Bounds,
    config: SceneConfig,
    path: Path,
) -> SpriteAsset:
    """Render the pin's key-light shadow alone.

    A single sun gives one clean, fully dense shadow whose strength the
    runtime scales, so the rim light, the world environment, and the board —
    which would shade the whole catcher — all sit out while the caster hides
    from camera rays.
    """
    framing = shadow_framing(
        bounds,
        pixels_per_unit=workshop.board.config.pixels_per_unit,
        sun_direction=config.lighting.key.direction,
        catcher_y=config.anatomy.background.pocket_y
        + trough_radius(
            board=workshop.board,
            plate=config.anatomy.plate,
        ),
        margin_pixels=config.assets.shadow_margin_pixels,
    )
    scene = workshop.scene
    catcher = workshop.shadow_catcher
    catcher.location = Vector((prototype.location.x, 0.0, 0.0))
    with (
        rendered(prototype, catcher),
        camera_ray_hidden(prototype),
        hidden(
            workshop.collections.background,
            workshop.collections.frame,
            workshop.rim_sun,
            workshop.fill_sun,
        ),
        world_disabled(scene),
    ):
        _render_sprite(
            workshop,
            prototype=prototype,
            framing=framing,
            config=config,
            path=path,
        )
    catcher.location = Vector((0.0, 0.0, 0.0))
    return SpriteAsset(
        image=path.name,
        size=framing.size,
        tip_anchor=framing.anchor,
    )
