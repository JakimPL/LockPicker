from dataclasses import dataclass
from typing import Final, List, Tuple

import numpy as np

from locksmith.assets.manifest.theme import ThemeManifest
from locksmith.assets.preview.compositing import _orientation_assets, _tip_target
from locksmith.schema.models.scene import SceneConfig
from locksmith.types import RGBAImage, TumblerState

_NOTICEABLE_DIFFERENCE: Final[int] = 2

PixelRect = Tuple[int, int, int, int]


@dataclass(frozen=True)
class CompositeMetrics:
    """Absolute 8-bit RGB differences between the composite and the still."""

    mean_absolute: float
    max_absolute: int
    noticeable_fraction: float


def _state_tinted_rects(
    manifest: ThemeManifest,
    *,
    config: SceneConfig,
) -> List[PixelRect]:
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
        rects.append(
            (left, top, left + orientation.size[0] * scale, top + orientation.size[1] * scale),
        )

    return rects


def _comparison_metrics(
    composite: RGBAImage,
    *,
    still: RGBAImage,
    excluded: List[PixelRect],
) -> CompositeMetrics:
    """Compare RGB channels outside the excluded regions.

    Raises:
        ValueError: when the composite and the still differ in size.
    """
    if composite.shape != still.shape:
        raise ValueError(f"composite {composite.shape} does not match still {still.shape}")

    mask = np.ones(composite.shape[:2], dtype=bool)
    for left, top, right, bottom in excluded:
        mask[max(top, 0) : max(bottom, 0), max(left, 0) : max(right, 0)] = False

    difference = np.abs(
        composite[:, :, :3].astype(np.int16) - still[:, :, :3].astype(np.int16),
    )
    selected = difference[mask]
    return CompositeMetrics(
        mean_absolute=float(selected.mean()),
        max_absolute=int(selected.max()),
        noticeable_fraction=float((selected > _NOTICEABLE_DIFFERENCE).mean()),
    )
