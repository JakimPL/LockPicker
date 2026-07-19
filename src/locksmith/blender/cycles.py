from typing import Iterable, Literal, Optional, Protocol, cast

import bpy
from bpy.types import Object, Scene

ComputeDeviceType = Literal["OPTIX", "CUDA", "CPU"]

_GPU_PREFERENCE_ORDER: tuple[ComputeDeviceType, ...] = ("OPTIX", "CUDA")


class CyclesSettings(Protocol):
    device: str
    samples: int
    seed: int
    use_denoising: bool
    denoiser: str


class _CyclesDevice(Protocol):
    type: str
    use: bool


class _CyclesPreferences(Protocol):
    compute_device_type: str

    def get_devices(self) -> None: ...

    @property
    def devices(self) -> Iterable[_CyclesDevice]: ...


def cycles_settings(scene: Scene) -> CyclesSettings:
    """Expose the Cycles render settings pointer with a typed shape.

    The Cycles addon registers `scene.cycles` at runtime, so the stubs only
    know it as an untyped attribute; the Protocol pins down the properties
    the build relies on.
    """
    settings: CyclesSettings = scene.cycles
    return settings


def enable_best_compute_device() -> ComputeDeviceType:
    """Activate the fastest available Cycles compute backend.

    OptiX leads the preference order for its RTX kernels; CUDA covers older
    NVIDIA setups; CPU always works. Assigning an unsupported device type
    raises TypeError, which moves the search to the next candidate.
    """
    preferences = _cycles_preferences()
    if preferences is None:
        return "CPU"

    for device_type in _GPU_PREFERENCE_ORDER:
        try:
            preferences.compute_device_type = device_type
        except TypeError:
            continue

        preferences.get_devices()
        found = False
        for device in preferences.devices:
            device.use = device.type == device_type
            found = found or device.use
        if found:
            return device_type

    return "CPU"


def _cycles_preferences() -> Optional[_CyclesPreferences]:
    """The Cycles addon preferences, or None when the addon is unavailable."""
    context_preferences = bpy.context.preferences
    if context_preferences is None:
        return None

    try:
        addon = context_preferences.addons["cycles"]
    except KeyError:
        return None

    return cast(_CyclesPreferences, addon.preferences)


def mark_shadow_catcher(catcher: Object) -> None:
    """Make the object collect shadows for compositing while staying invisible itself."""
    catcher.is_shadow_catcher = True
