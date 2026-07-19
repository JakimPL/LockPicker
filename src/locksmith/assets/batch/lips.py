from pathlib import Path

from bpy.types import Object

from locksmith.assets.batch.constants import _LIP_FILENAME
from locksmith.assets.batch.sprite import _render_prototype_sprite
from locksmith.assets.framing import strip_framing
from locksmith.assets.manifest.lips import LipAssets
from locksmith.assets.manifest.sprite import SpriteAsset
from locksmith.blender.objects import local_bounds
from locksmith.builder import WorkshopScene
from locksmith.schema.models.scene import SceneConfig


def _render_lips(
    workshop: WorkshopScene,
    *,
    config: SceneConfig,
    directory: Path,
) -> LipAssets:
    """Render both shear-lip strips on full-board-width canvases.

    Each orientation bakes separately because the upper-left key sun lights
    the two lips' bevels differently.
    """
    return LipAssets(
        upper=_render_lip(
            workshop.lip_upper,
            workshop=workshop,
            config=config,
            path=directory / _LIP_FILENAME.format(orientation="upper"),
        ),
        lower=_render_lip(
            workshop.lip_lower,
            workshop=workshop,
            config=config,
            path=directory / _LIP_FILENAME.format(orientation="lower"),
        ),
    )


def _render_lip(
    lip: Object,
    *,
    workshop: WorkshopScene,
    config: SceneConfig,
    path: Path,
) -> SpriteAsset:
    framing = strip_framing(
        local_bounds(lip),
        pixels_per_unit=workshop.board.config.pixels_per_unit,
        width_pixels=workshop.board.config.width_pixels,
        padding_pixels=config.assets.padding_pixels,
    )
    return _render_prototype_sprite(workshop, prototype=lip, framing=framing, config=config, path=path)
