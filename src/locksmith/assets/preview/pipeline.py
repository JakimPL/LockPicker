from dataclasses import dataclass
from pathlib import Path
from typing import Final, Optional

from locksmith.assets.manifest.theme import ThemeManifest
from locksmith.assets.png import write_rgba
from locksmith.assets.preview.compositing import compose_board
from locksmith.assets.preview.loading import _load_sprites
from locksmith.assets.preview.metrics import CompositeMetrics, _comparison_metrics, _state_tinted_rects
from locksmith.blender.images import read_rgba_pixels
from locksmith.schema.models.scene import SceneConfig

PREVIEW_FILENAME: Final[str] = "composite_preview.png"


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
        metrics = _comparison_metrics(
            composite,
            still=still,
            excluded=_state_tinted_rects(manifest, config=config),
        )
    return PreviewResult(preview_path=preview_path, metrics=metrics)
