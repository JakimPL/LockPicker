from pathlib import Path

from bpy.types import Object
from mathutils import Vector

from locksmith.assets.batch.constants import _BADGE_FILENAME
from locksmith.assets.batch.sprite import _framed, _render_prototype_sprite, _slot_x
from locksmith.assets.manifest.badge import BadgeAsset
from locksmith.assets.manifest.badges import BadgesAssets
from locksmith.builder import WorkshopScene
from locksmith.schema.models.scene import SceneConfig


def _render_badges(
    workshop: WorkshopScene,
    *,
    config: SceneConfig,
    directory: Path,
) -> BadgesAssets:
    prototype: Object = workshop.prototypes.badge
    prototype.location = Vector((_slot_x(workshop), 0.0, 0.0))
    framing = _framed(prototype, workshop=workshop, config=config)
    sprite = _render_prototype_sprite(
        workshop,
        prototype=prototype,
        framing=framing,
        config=config,
        path=directory / _BADGE_FILENAME,
    )
    master = BadgeAsset(
        image=sprite.image,
        size=sprite.size,
        center_anchor=sprite.tip_anchor,
        tip_offset_pixels=config.assets.badge_tip_offset_pixels,
    )
    return BadgesAssets(master=master)
