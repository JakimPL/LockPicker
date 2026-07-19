# TODO: split into subpackages

from pathlib import Path
from typing import Dict, Final

from bpy.types import Object, Scene
from mathutils import Vector

from locksmith.assets.framing import (
    Bounds,
    SpriteFraming,
    shadow_framing,
    sprite_framing,
    strip_framing,
)
from locksmith.assets.manifest.badge import BadgeAsset
from locksmith.assets.manifest.badges import BadgesAssets
from locksmith.assets.manifest.board import BoardAssets
from locksmith.assets.manifest.lips import LipAssets
from locksmith.assets.manifest.provenance import RenderProvenance
from locksmith.assets.manifest.sprite import SpriteAsset
from locksmith.assets.manifest.theme import (
    MANIFEST_FILENAME,
    ThemeManifest,
    write_manifest,
)
from locksmith.assets.manifest.tumbler_orientation import TumblerOrientationAssets
from locksmith.assets.manifest.tumblers import TumblerAssets
from locksmith.assets.png import require_png_size
from locksmith.blender.cameras import new_orthographic_camera
from locksmith.blender.objects import (
    local_bounds,
    override_slot_material,
    set_camera_ray_visibility,
)
from locksmith.blender.scene_state import (
    camera_ray_hidden,
    camera_ray_visible,
    film_transparent,
    hidden,
    rendered,
    world_disabled,
)
from locksmith.blender.session import blender_version, render_still
from locksmith.builder import WorkshopScene
from locksmith.parts.background import trough_radius
from locksmith.rendering.cameras import FACING_BOARD
from locksmith.schema.models.scene import SceneConfig
from locksmith.types import Metal, PickShape, PixelPair

_SCHEMA_VERSION: Final[int] = 2
_ENGINE: Final[str] = "CYCLES"
_BACKGROUND_FILENAME: Final[str] = "background.png"
_FRAME_FILENAME: Final[str] = "frame.png"
_BADGE_FILENAME: Final[str] = "badge_master.png"
_SHADOW_FILENAME: Final[str] = "shadow_{orientation}.png"
_PIN_FILENAME: Final[str] = "pin_{metal}_{orientation}.png"
_PICK_FILENAME: Final[str] = "pick_{shape}.png"
_LIP_FILENAME: Final[str] = "lip_{orientation}.png"
_CAMERA_PREFIX: Final[str] = "CAM_"


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


def _render_board(
    workshop: WorkshopScene,
    *,
    config: SceneConfig,
    directory: Path,
) -> BoardAssets:
    """Render the opaque back layer and the transparent overlay plate.

    The back layer is the empty mechanism: the diffuse channel wall carries
    the plate's static shadowing even though the plate itself stays out of
    the image, so pins composite over exactly the wall the still shows
    around them.
    """
    logical = _logical_board_size(config)
    scale = config.assets.image_scale
    scene = workshop.scene
    scene.camera = workshop.board_camera
    _set_canvas(scene, size=logical, image_scale=scale)

    with camera_ray_visible(workshop.background_wall), film_transparent(scene, transparent=False):
        _render_file(scene, directory / _BACKGROUND_FILENAME, expected=_scaled(logical, scale))

    statics = (
        workshop.frame_plate,
        workshop.bench,
        workshop.keyway,
        workshop.flanges,
        workshop.screws,
    )
    with camera_ray_visible(*statics), film_transparent(scene, transparent=True):
        _render_file(scene, directory / _FRAME_FILENAME, expected=_scaled(logical, scale))

    return BoardAssets(
        logical_size=logical,
        background=_BACKGROUND_FILENAME,
        frame=_FRAME_FILENAME,
    )


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


def _render_picks(
    workshop: WorkshopScene,
    *,
    config: SceneConfig,
    directory: Path,
) -> Dict[PickShape, SpriteAsset]:
    prototypes = {
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


def _render_badges(
    workshop: WorkshopScene,
    *,
    config: SceneConfig,
    directory: Path,
) -> BadgesAssets:
    prototype = workshop.prototypes.badge
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


def _slot_x(workshop: WorkshopScene) -> float:
    """Center of the middle column; sprite passes render inside a real slot.

    Slots repeat identically per column and run uniformly past the visible
    board, so the baked surroundings stay valid wherever the sprite
    translates at runtime.
    """
    return workshop.board.column_center_x(workshop.board.config.columns // 2)


def _logical_board_size(config: SceneConfig) -> PixelPair:
    """The board size as whole pixels.

    Raises:
        ValueError: when the configured board size is fractional.
    """
    width = config.board.width_pixels
    height = config.board.height_pixels
    if not width.is_integer() or not height.is_integer():
        raise ValueError(f"board size {width}x{height} is not a whole pixel count")
    return int(width), int(height)


def _scaled(size: PixelPair, image_scale: int) -> PixelPair:
    return size[0] * image_scale, size[1] * image_scale


def _set_canvas(scene: Scene, *, size: PixelPair, image_scale: int) -> None:
    scene.render.resolution_x = size[0] * image_scale
    scene.render.resolution_y = size[1] * image_scale


def _render_file(scene: Scene, path: Path, *, expected: PixelPair) -> None:
    render_still(scene, path)
    require_png_size(path, expected)
    print(f"rendered: {path.name} ({expected[0]}x{expected[1]})")
