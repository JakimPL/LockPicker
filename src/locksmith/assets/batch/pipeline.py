from pathlib import Path

from locksmith.assets.batch.badges import _render_badges
from locksmith.assets.batch.board import _render_board
from locksmith.assets.batch.constants import _ENGINE, _SCHEMA_VERSION
from locksmith.assets.batch.lips import _render_lips
from locksmith.assets.batch.picks import _render_picks
from locksmith.assets.batch.tumblers import _render_tumbler_orientation
from locksmith.assets.manifest.provenance import RenderProvenance
from locksmith.assets.manifest.theme import MANIFEST_FILENAME, ThemeManifest, write_manifest
from locksmith.assets.manifest.tumblers import TumblerAssets
from locksmith.blender.objects import set_camera_ray_visibility
from locksmith.blender.session import blender_version
from locksmith.builder import WorkshopScene
from locksmith.schema.models.scene import SceneConfig


def render_assets(workshop: WorkshopScene, *, config: SceneConfig, directory: Path) -> ThemeManifest:
    """Render every theme asset into the directory and write its manifest.

    This is the only writer of manifest.json, so the images and the metadata
    describing them can never drift apart. Every view transform matches the
    look-dev still — sprites must color-match the background they composite
    onto. The passes mutate the freshly built scene (visibility, materials,
    cameras) and leave it dirty; rerunning rebuilds from scratch.
    """
    directory.mkdir(parents=True, exist_ok=True)
    workshop.collections.lookdev.hide_render = True
    workshop.lip_upper.hide_render = True
    workshop.lip_lower.hide_render = True
    _expose_board_to_secondary_rays(workshop)

    board = _render_board(workshop, config=config, directory=directory)
    tumblers = TumblerAssets(
        full_height_units=workshop.board.config.max_height,
        pixels_per_height_unit=workshop.board.config.pixels_per_unit,
        column_width_pixels=workshop.board.config.column_width_pixels,
        groups=config.assets.groups,
        upper=_render_tumbler_orientation(workshop, upper=True, config=config, directory=directory),
        lower=_render_tumbler_orientation(workshop, upper=False, config=config, directory=directory),
    )
    picks = _render_picks(workshop, config=config, directory=directory)
    badges = _render_badges(workshop, config=config, directory=directory)
    lips = _render_lips(workshop, config=config, directory=directory)

    manifest = ThemeManifest(
        schema_version=_SCHEMA_VERSION,
        theme=config.assets.theme,
        image_scale=config.assets.image_scale,
        provenance=RenderProvenance(
            blender_version=blender_version(),
            engine=_ENGINE,
            samples=config.render.samples,
            seed=config.render.seed,
            view_transform=config.render.view_transform,
            look=workshop.render_settings.look,
            exposure=config.render.exposure,
        ),
        board=board,
        tumblers=tumblers,
        picks=picks,
        badges=badges,
        lips=lips,
    )
    write_manifest(manifest, directory / MANIFEST_FILENAME)
    return manifest


def _expose_board_to_secondary_rays(workshop: WorkshopScene) -> None:
    """Keep the static board in reflections and bounce light for sprite passes.

    Sprites must bake the same surroundings the still shows — a pin in its
    slot reflects the dark plate around it, not the open sky — so the board
    geometry stays in the scene but leaves the camera image and its alpha to
    the sprite alone.
    """
    workshop.collections.background.hide_render = False
    workshop.collections.frame.hide_render = False
    for static in (
        workshop.background_wall,
        workshop.frame_plate,
        workshop.sprite_stage,
        workshop.bench,
        workshop.keyway,
        workshop.flanges,
        workshop.screws,
    ):
        set_camera_ray_visibility(static, visible=False)
