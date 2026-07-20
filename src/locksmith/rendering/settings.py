from dataclasses import dataclass
from typing import Final, Tuple

from bpy.types import ColorManagedViewSettings, Scene

from locksmith.blender.cycles import (
    ComputeDeviceType,
    CyclesSettings,
    cycles_settings,
    enable_best_compute_device,
)
from locksmith.schema.models.rendering import RenderConfig

_FILE_FORMAT: Final[str] = "PNG"
_COLOR_MODE: Final[str] = "RGBA"
_COLOR_DEPTH: Final[str] = "8"
_FULL_RESOLUTION_PERCENTAGE: Final[int] = 100


@dataclass(frozen=True)
class AppliedRenderSettings:
    """Resolved render choices the config alone cannot pin down."""

    device_type: ComputeDeviceType
    look: str


def apply_render_settings(
    scene: Scene,
    config: RenderConfig,
) -> AppliedRenderSettings:
    device_type = _apply_engine_and_device(scene)
    _apply_sampling(scene, config, device_type=device_type)
    _apply_output_dimensions(scene, config)
    _apply_image_format(scene)
    look = _apply_color_management(scene, config)
    return AppliedRenderSettings(device_type=device_type, look=look)


def _apply_engine_and_device(scene: Scene) -> ComputeDeviceType:
    scene.render.engine = "CYCLES"
    device_type = enable_best_compute_device()
    settings = cycles_settings(scene)
    settings.device = "CPU" if device_type == "CPU" else "GPU"
    return device_type


def _apply_sampling(scene: Scene, config: RenderConfig, *, device_type: ComputeDeviceType) -> None:
    settings = cycles_settings(scene)
    settings.samples = config.samples
    settings.seed = config.seed
    settings.use_denoising = config.use_denoising
    _apply_denoiser(settings, device_type)


def _apply_output_dimensions(scene: Scene, config: RenderConfig) -> None:
    width, height = config.resolution
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = _FULL_RESOLUTION_PERCENTAGE
    scene.render.film_transparent = config.film_transparent


def _apply_image_format(scene: Scene) -> None:
    image_settings = scene.render.image_settings
    image_settings.file_format = _FILE_FORMAT
    image_settings.color_mode = _COLOR_MODE
    image_settings.color_depth = _COLOR_DEPTH


def _apply_color_management(scene: Scene, config: RenderConfig) -> str:
    view_settings = _require_view_settings(scene)
    view_settings.view_transform = config.view_transform
    view_settings.exposure = config.exposure
    return _apply_first_supported_look(scene, config.look_candidates)


def _apply_denoiser(
    settings: CyclesSettings,
    device_type: ComputeDeviceType,
) -> None:
    """Denoise on the render device when it is OptiX; otherwise use OpenImageDenoise.

    Assigning an unsupported denoiser raises TypeError, so the OptiX attempt
    falls back to the universally available OpenImageDenoise.
    """
    if device_type == "OPTIX":
        try:
            settings.denoiser = "OPTIX"
            return
        except TypeError:
            pass

    settings.denoiser = "OPENIMAGEDENOISE"


def _require_view_settings(scene: Scene) -> ColorManagedViewSettings:
    """Return the scene's color management settings.

    Raises:
        RuntimeError: when the scene carries no view settings.
    """
    view_settings = scene.view_settings
    if view_settings is None:
        raise RuntimeError("scene has no color management view settings")

    return view_settings


def _apply_first_supported_look(
    scene: Scene,
    candidates: Tuple[str, ...],
) -> str:
    """Apply the first color-management look this Blender build supports.

    Look names have shifted across Blender releases ("AgX - Base Contrast"
    vs "Base Contrast"), so the config lists candidates in preference order;
    assigning an unknown look raises TypeError and the next candidate is
    tried. Returns the applied look for the manifest's render provenance.

    Raises:
        RuntimeError: when no candidate is supported.
    """
    view_settings = _require_view_settings(scene)
    for look in candidates:
        try:
            view_settings.look = look
        except TypeError:
            continue

        return look

    raise RuntimeError(f"no supported color management look among {candidates}")
