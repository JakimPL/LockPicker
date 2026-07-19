from typing import Dict, Final, Tuple

import numpy as np

from locksmith.assets.manifest.theme import ThemeManifest
from locksmith.assets.manifest.tumbler_orientation import TumblerOrientationAssets
from locksmith.lookdev import hovered_tumbler
from locksmith.schema.models.board import BoardConfig
from locksmith.schema.models.lookdev.tumbler import TumblerPlacement
from locksmith.schema.models.scene import SceneConfig
from locksmith.types import PickShape, PixelPair, RGBAImage, TumblerState

_OPAQUE: Final[int] = 255


def compose_board(
    manifest: ThemeManifest,
    *,
    config: SceneConfig,
    sprites: Dict[str, RGBAImage],
    include_shadows: bool,
) -> RGBAImage:
    """Blend the layers exactly as the runtime will: 8-bit alpha-over in draw order.

    The order is background, shadows, pins, badges, frame, picks — the frame
    plate masks pin and shadow overflow beyond the slots, and picks travel in
    front of the plate. Hover and jam tumblers composite with their base
    metal sprites; those states are runtime tints outside the baked assets.
    """
    canvas = sprites[manifest.board.background].copy()
    scale = manifest.image_scale
    if include_shadows:
        for placement in config.lookdev.tumblers:
            shadow = _orientation_assets(manifest, upper=placement.upper).shadow
            _blit_anchored(
                canvas,
                sprites[shadow.image],
                anchor=shadow.tip_anchor,
                target=_tip_target(placement, board=config.board),
                image_scale=scale,
            )

    for placement in config.lookdev.tumblers:
        orientation = _orientation_assets(manifest, upper=placement.upper)
        _blit_anchored(
            canvas,
            sprites[orientation.images[placement.metal]],
            anchor=orientation.tip_anchor,
            target=_tip_target(placement, board=config.board),
            image_scale=scale,
        )

    badge = manifest.badges.master
    for placement in config.lookdev.tumblers:
        if placement.state is not TumblerState.MASTER:
            continue
        center_x, tip_y = _tip_target(placement, board=config.board)
        badge_y = tip_y - badge.tip_offset_pixels if placement.upper else tip_y + badge.tip_offset_pixels
        _blit_anchored(
            canvas,
            sprites[badge.image],
            anchor=badge.center_anchor,
            target=(center_x, badge_y),
            image_scale=scale,
        )

    _blit_anchored(
        canvas,
        sprites[manifest.board.frame],
        anchor=(0, 0),
        target=(0.0, 0.0),
        image_scale=scale,
    )
    _blit_lips(canvas, manifest, config=config, sprites=sprites)
    _blit_picks(canvas, manifest, config=config, sprites=sprites)
    return canvas


def _blit_lips(
    canvas: RGBAImage,
    manifest: ThemeManifest,
    *,
    config: SceneConfig,
    sprites: Dict[str, RGBAImage],
) -> None:
    """Place both shear-lip strips one height unit inside their board edges."""
    scale = manifest.image_scale
    center_x = config.board.width_pixels / 2
    for upper, lip in ((True, manifest.lips.upper), (False, manifest.lips.lower)):
        travel = config.board.pixels_per_unit
        line_y = travel if upper else config.board.height_pixels - travel
        _blit_anchored(
            canvas,
            sprites[lip.image],
            anchor=lip.tip_anchor,
            target=(center_x, line_y),
            image_scale=scale,
        )


def _blit_picks(
    canvas: RGBAImage,
    manifest: ThemeManifest,
    *,
    config: SceneConfig,
    sprites: Dict[str, RGBAImage],
) -> None:
    """Place the engaged diamond pick on the hovered tumbler and the idle circle pick."""
    scale = manifest.image_scale
    hovered = hovered_tumbler(config.lookdev)
    engaged = manifest.picks[PickShape.DIAMOND]
    center_x, tip_y = _tip_target(hovered, board=config.board)
    bite = config.lookdev.engaged_pick.bite_pixels
    engaged_y = tip_y + bite if hovered.upper else tip_y - bite
    _blit_anchored(
        canvas,
        sprites[engaged.image],
        anchor=engaged.tip_anchor,
        target=(center_x, engaged_y),
        image_scale=scale,
    )
    idle = manifest.picks[PickShape.CIRCLE]
    idle_y = config.board.height_pixels / 2 - config.lookdev.idle_pick.z_pixels
    _blit_anchored(
        canvas,
        sprites[idle.image],
        anchor=idle.tip_anchor,
        target=(config.lookdev.idle_pick.x_pixels, idle_y),
        image_scale=scale,
    )


def _orientation_assets(
    manifest: ThemeManifest,
    *,
    upper: bool,
) -> TumblerOrientationAssets:
    return manifest.tumblers.upper if upper else manifest.tumblers.lower


def _tip_target(
    placement: TumblerPlacement,
    *,
    board: BoardConfig,
) -> Tuple[float, float]:
    """Logical pixel position of the tumbler's free tip; image y grows downward."""
    center_x = (
        board.column_offset_pixels + placement.position * board.column_pitch_pixels + board.column_width_pixels / 2
    )
    travel = placement.height * board.pixels_per_unit
    tip_y = travel if placement.upper else board.height_pixels - travel
    return center_x, tip_y


def _blit_anchored(
    canvas: RGBAImage,
    sprite: RGBAImage,
    *,
    anchor: PixelPair,
    target: Tuple[float, float],
    image_scale: int,
) -> None:
    left = (round(target[0]) - anchor[0]) * image_scale
    top = (round(target[1]) - anchor[1]) * image_scale
    _alpha_over(canvas, sprite, left=left, top=top)


def _alpha_over(
    canvas: RGBAImage,
    sprite: RGBAImage,
    *,
    left: int,
    top: int,
) -> None:
    """In-place 8-bit alpha blend with clipping, matching a PyGame alpha blit."""
    sprite_height, sprite_width = sprite.shape[0], sprite.shape[1]
    canvas_height, canvas_width = canvas.shape[0], canvas.shape[1]
    x_start = max(left, 0)
    y_start = max(top, 0)
    x_stop = min(left + sprite_width, canvas_width)
    y_stop = min(top + sprite_height, canvas_height)
    if x_start >= x_stop or y_start >= y_stop:
        return
    patch = sprite[y_start - top : y_stop - top, x_start - left : x_stop - left]
    alpha = patch[:, :, 3:4].astype(np.uint16)
    region = canvas[y_start:y_stop, x_start:x_stop, :3].astype(np.uint16)
    foreground = patch[:, :, :3].astype(np.uint16)
    blended = (foreground * alpha + region * (_OPAQUE - alpha) + _OPAQUE // 2) // _OPAQUE
    canvas[y_start:y_stop, x_start:x_stop, :3] = blended.astype(np.uint8)
