from bpy.types import Material

from locksmith.blender.materials import new_principled_material
from locksmith.blender.nodes import (
    link_bump_normal,
    new_banded_wave,
    output_socket,
    set_color_input,
    set_float_input,
)
from locksmith.colors import linear_rgba, scaled
from locksmith.schema.models.shading.grip import GripConfig
from locksmith.types import HexColor


def make_grip_material(
    name: str,
    *,
    color: HexColor,
    config: GripConfig,
) -> Material:
    """Waxed cord wrap: banded wave bump across the shaft, palette color dimmed to scene values."""
    material, node_tree, principled = new_principled_material(name)
    set_color_input(principled, "Base Color", linear_rgba(scaled(color, config.dim_factor)))
    set_float_input(principled, "Roughness", config.roughness)
    wave = new_banded_wave(node_tree, scale=config.wave_scale)
    link_bump_normal(node_tree, principled, height=output_socket(wave, "Fac"), strength=config.bump_strength)
    return material
