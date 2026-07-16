from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Final, List, Optional, Tuple

import numpy as np

from locksmith.assets.manifest.theme import ThemeManifest
from locksmith.assets.manifest.tumbler_orientation import TumblerOrientationAssets
from locksmith.assets.png import write_rgba
from locksmith.blender.images import read_rgba_pixels
from locksmith.config.models.board import BoardConfig
from locksmith.config.models.lookdev.tumbler import TumblerPlacement
from locksmith.config.models.scene import SceneConfig
from locksmith.lookdev import hovered_tumbler
from locksmith.types import PickShape, PixelPair, RGBAImage, TumblerState

PREVIEW_FILENAME: Final[str] = "composite_preview.png"
_NOTICEABLE_DIFFERENCE: Final[int] = 2
_OPAQUE: Final[int] = 255

PixelRect = Tuple[int, int, int, int]


@dataclass(frozen=True)
class CompositeMetrics:
    """Absolute 8-bit RGB differences between the composite and the still."""

    mean_absolute: float
    max_absolute: int
    noticeable_fraction: float


@dataclass(frozen=True)
class PreviewResult:
    preview_path: Path
    metrics: Optional[CompositeMetrics]


def render_preview(
    manifest: ThemeManifest,
    *,
    config: SceneConfig,
    theme_directory: Path,
    output_directory: Path,
    still_path: Path,
) -> PreviewResult:
    """Composite the look-dev arrangement from the rendered sprites.

    The composite stacks the full runtime draw order and is compared against
    the approved still to bound the sprite pipeline's error: anchor math,
    edge fringing, the mid-travel bake of position-dependent reflections,
    and the single-sun shadow approximation of the real pin-to-wall shadows.
    """
    sprites = _load_sprites(manifest, theme_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    preview_path = output_directory / PREVIEW_FILENAME
    composite = compose_board(manifest, config=config, sprites=sprites, include_shadows=True)
    write_rgba(preview_path, composite)
    metrics: Optional[CompositeMetrics] = None
    if still_path.exists():
        still = read_rgba_pixels(still_path)
        metrics = _comparison_metrics(composite, still=still, excluded=_state_tinted_rects(manifest, config=config))
    return PreviewResult(preview_path=preview_path, metrics=metrics)


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
    _blit_anchored(canvas, sprites[manifest.board.frame], anchor=(0, 0), target=(0.0, 0.0), image_scale=scale)
    _blit_picks(canvas, manifest, config=config, sprites=sprites)
    return canvas


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
        canvas, sprites[engaged.image], anchor=engaged.tip_anchor, target=(center_x, engaged_y), image_scale=scale
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


def _load_sprites(manifest: ThemeManifest, directory: Path) -> Dict[str, RGBAImage]:
    filenames = {manifest.board.background, manifest.board.frame, manifest.badges.master.image}
    for orientation in (manifest.tumblers.upper, manifest.tumblers.lower):
        filenames.update(orientation.images.values())
        filenames.add(orientation.shadow.image)
    filenames.update(pick.image for pick in manifest.picks.values())
    return {filename: read_rgba_pixels(directory / filename) for filename in sorted(filenames)}


def _orientation_assets(manifest: ThemeManifest, *, upper: bool) -> TumblerOrientationAssets:
    return manifest.tumblers.upper if upper else manifest.tumblers.lower


def _tip_target(placement: TumblerPlacement, *, board: BoardConfig) -> Tuple[float, float]:
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


def _alpha_over(canvas: RGBAImage, sprite: RGBAImage, *, left: int, top: int) -> None:
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


def _state_tinted_rects(manifest: ThemeManifest, *, config: SceneConfig) -> List[PixelRect]:
    """Image regions where the still shows hover or jam materials.

    The parity composite can only use base metal sprites there, so these
    regions stay out of the comparison metrics.
    """
    rects: List[PixelRect] = []
    scale = manifest.image_scale
    for placement in config.lookdev.tumblers:
        if placement.state not in (TumblerState.HOVER, TumblerState.JAM):
            continue
        orientation = _orientation_assets(manifest, upper=placement.upper)
        center_x, tip_y = _tip_target(placement, board=config.board)
        left = (round(center_x) - orientation.tip_anchor[0]) * scale
        top = (round(tip_y) - orientation.tip_anchor[1]) * scale
        rects.append((left, top, left + orientation.size[0] * scale, top + orientation.size[1] * scale))
    return rects


def _comparison_metrics(composite: RGBAImage, *, still: RGBAImage, excluded: List[PixelRect]) -> CompositeMetrics:
    """Compare RGB channels outside the excluded regions.

    Raises:
        ValueError: when the composite and the still differ in size.
    """
    if composite.shape != still.shape:
        raise ValueError(f"composite {composite.shape} does not match still {still.shape}")
    mask = np.ones(composite.shape[:2], dtype=bool)
    for left, top, right, bottom in excluded:
        mask[max(top, 0) : max(bottom, 0), max(left, 0) : max(right, 0)] = False
    difference = np.abs(composite[:, :, :3].astype(np.int16) - still[:, :, :3].astype(np.int16))
    selected = difference[mask]
    return CompositeMetrics(
        mean_absolute=float(selected.mean()),
        max_absolute=int(selected.max()),
        noticeable_fraction=float((selected > _NOTICEABLE_DIFFERENCE).mean()),
    )
