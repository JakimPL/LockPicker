from bpy.types import Material, ShaderNodeBump, ShaderNodeTexWave

from locksmith.blender.materials import new_principled_material
from locksmith.blender.nodes import (
    link_nodes,
    new_node,
    set_color_input,
    set_float_input,
)
from locksmith.colors import linear_rgba, scaled
from locksmith.schema.models.shading.grip import GripConfig
from locksmith.types import HexColor


# TODO: refactor
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
    wave = new_node(node_tree, ShaderNodeTexWave)
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    set_float_input(wave, "Scale", config.wave_scale)
    bump = new_node(node_tree, ShaderNodeBump)
    set_float_input(bump, "Strength", config.bump_strength)
    link_nodes(node_tree, source=(wave, "Fac"), target=(bump, "Height"))
    link_nodes(node_tree, source=(bump, "Normal"), target=(principled, "Normal"))
    return material
