from pathlib import Path
from typing import Dict

from bpy.types import Object
from mathutils import Vector

from locksmith.assets.batch.constants import _PICK_FILENAME
from locksmith.assets.batch.sprite import _framed, _render_prototype_sprite, _slot_x
from locksmith.assets.manifest.sprite import SpriteAsset
from locksmith.builder import WorkshopScene
from locksmith.schema.models.scene import SceneConfig
from locksmith.types import PickShape


def _render_picks(
    workshop: WorkshopScene,
    *,
    config: SceneConfig,
    directory: Path,
) -> Dict[PickShape, SpriteAsset]:
    prototypes: Dict[PickShape, Object] = {
        PickShape.DIAMOND: workshop.prototypes.pick_diamond,
        PickShape.CIRCLE: workshop.prototypes.pick_circle,
    }
    picks: Dict[PickShape, SpriteAsset] = {}
    for shape, prototype in prototypes.items():
        prototype.location = Vector(
            (
                _slot_x(workshop),
                config.lookdev.engaged_pick.y,
                0.0,
            )
        )
        framing = _framed(prototype, workshop=workshop, config=config)
        picks[shape] = _render_prototype_sprite(
            workshop,
            prototype=prototype,
            framing=framing,
            config=config,
            path=directory / _PICK_FILENAME.format(shape=shape.value),
        )

    return picks
