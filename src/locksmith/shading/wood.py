from bpy.types import (
    Material,
    ShaderNodeBump,
    ShaderNodeMapping,
    ShaderNodeTexCoord,
    ShaderNodeTexNoise,
    ShaderNodeTexWave,
)

from locksmith.blender.materials import new_principled_material
from locksmith.blender.nodes import (
    MIX_A,
    MIX_FACTOR,
    MIX_RESULT,
    input_by_identifier,
    input_socket,
    link_nodes,
    link_sockets,
    new_color_mix_node,
    new_math_node,
    new_node,
    output_by_identifier,
    output_socket,
    set_float_input,
    set_vector_input,
)
from locksmith.colors import linear_rgba
from locksmith.schema.models.palette.palette import PaletteConfig
from locksmith.schema.models.shading.wood import WoodConfig


def make_wood_material(name: str, *, palette: PaletteConfig, config: WoodConfig) -> Material:
    """Oiled bench wood: distorted wave grain stretched into vertical streaks.

    Unlike the emission plate this is a lit PBR surface, so the key sun and
    the plank depth jitter shade it for real — the panels keep depth instead
    of reading as a painted gradient. The grain wave also drives a soft bump
    so the surface catches the light unevenly.
    """
    material, node_tree, principled = new_principled_material(name)
    set_float_input(principled, "Specular IOR Level", config.specular)
    set_float_input(principled, "Roughness", config.roughness)

    coordinates = new_node(node_tree, ShaderNodeTexCoord)
    mapping = new_node(node_tree, ShaderNodeMapping)
    set_vector_input(mapping, "Scale", (1.0, 1.0, config.stretch))
    link_nodes(node_tree, source=(coordinates, "Object"), target=(mapping, "Vector"))

    grain_wave = new_node(node_tree, ShaderNodeTexWave)
    grain_wave.wave_type = "BANDS"
    grain_wave.bands_direction = "X"
    set_float_input(grain_wave, "Scale", config.ring_scale)
    set_float_input(grain_wave, "Distortion", config.distortion)
    set_float_input(grain_wave, "Detail", config.ring_detail)
    link_nodes(node_tree, source=(mapping, "Vector"), target=(grain_wave, "Vector"))

    grain = new_color_mix_node(node_tree, a=linear_rgba(palette.wood), b=linear_rgba(palette.wood_dark))
    link_sockets(node_tree, output_socket(grain_wave, "Fac"), input_by_identifier(grain, MIX_FACTOR))

    tone = new_node(node_tree, ShaderNodeTexNoise)
    set_float_input(tone, "Scale", config.tone_scale)
    set_float_input(tone, "Detail", config.tone_detail)
    link_nodes(node_tree, source=(coordinates, "Object"), target=(tone, "Vector"))
    tone_strength = new_math_node(node_tree, "MULTIPLY", operand=config.tone_strength)
    link_nodes(node_tree, source=(tone, "Fac"), target=(tone_strength, "Value"))
    toned = new_color_mix_node(node_tree, a=None, b=linear_rgba(palette.wood_dark))
    link_sockets(node_tree, output_by_identifier(grain, MIX_RESULT), input_by_identifier(toned, MIX_A))
    link_sockets(node_tree, output_socket(tone_strength, "Value"), input_by_identifier(toned, MIX_FACTOR))
    link_sockets(node_tree, output_by_identifier(toned, MIX_RESULT), input_socket(principled, "Base Color"))

    bump = new_node(node_tree, ShaderNodeBump)
    set_float_input(bump, "Strength", config.bump_strength)
    link_nodes(node_tree, source=(grain_wave, "Fac"), target=(bump, "Height"))
    link_nodes(node_tree, source=(bump, "Normal"), target=(principled, "Normal"))
    return material
