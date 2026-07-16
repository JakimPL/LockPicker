from dataclasses import dataclass
from typing import Final, Tuple

from bpy.types import ColorManagedViewSettings, Scene

from locksmith.blender.cycles import ComputeDeviceType, CyclesSettings, cycles_settings, enable_best_compute_device
from locksmith.config.models.rendering import RenderConfig

_FILE_FORMAT: Final[str] = "PNG"
_COLOR_MODE: Final[str] = "RGBA"
_COLOR_DEPTH: Final[str] = "8"
_FULL_RESOLUTION_PERCENTAGE: Final[int] = 100


@dataclass(frozen=True)
class AppliedRenderSettings:
    """Resolved render choices the config alone cannot pin down."""

    device_type: ComputeDeviceType
    look: str


def apply_render_settings(scene: Scene, config: RenderConfig) -> AppliedRenderSettings:
    # The stubs type the dynamic engine enum with only the built-in default,
    # so choosing Cycles needs a coded exception.
    scene.render.engine = "CYCLES"  # type: ignore[assignment]
    device_type = enable_best_compute_device()
    settings = cycles_settings(scene)
    settings.device = "CPU" if device_type == "CPU" else "GPU"
    settings.samples = config.samples
    settings.seed = config.seed
    settings.use_denoising = config.use_denoising
    _apply_denoiser(settings, device_type)

    width, height = config.resolution
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = _FULL_RESOLUTION_PERCENTAGE
    scene.render.film_transparent = config.film_transparent
    image_settings = scene.render.image_settings
    # The stubs type the format enums with only their empty defaults.
    image_settings.file_format = _FILE_FORMAT  # type: ignore[assignment]
    image_settings.color_mode = _COLOR_MODE  # type: ignore[assignment]
    image_settings.color_depth = _COLOR_DEPTH  # type: ignore[assignment]

    view_settings = _require_view_settings(scene)
    # The stubs type the dynamic OCIO enums with only their empty default.
    view_settings.view_transform = config.view_transform  # type: ignore[assignment]
    view_settings.exposure = config.exposure
    look = _apply_first_supported_look(scene, config.look_candidates)
    return AppliedRenderSettings(device_type=device_type, look=look)


def _apply_denoiser(settings: CyclesSettings, device_type: ComputeDeviceType) -> None:
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
            # The stubs type the dynamic OCIO enums with only their empty default.
            view_settings.look = look  # type: ignore[assignment]
        except TypeError:
            continue

        return look

    raise RuntimeError(f"no supported color management look among {candidates}")
