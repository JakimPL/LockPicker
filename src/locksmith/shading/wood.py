from bpy.types import (
    Material,
    NodeTree,
    ShaderNodeBsdfPrincipled,
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
    input_socket_at,
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
    """Figured oiled hardwood: broad cathedral tone under thin latewood lines.

    Two grain scales keep the panel from reading as flat ribbed board. A slow
    anisotropic noise, streaked along the plank, lifts the earlywood zones
    toward a lighter warm tone so wide figure wanders board to board; a faster
    distorted wave then lays thin darker latewood lines over it, mixed only
    partway to the dark stain so they stay accents rather than an even
    corduroy. The lines also break the roughness — latewood reads a touch
    glossier — so the key sun's highlight travels the grain instead of sitting
    flat, and a soft bump follows the same lines for real relief.
    """
    material, node_tree, principled = new_principled_material(name)
    set_float_input(principled, "Specular IOR Level", config.specular)

    coordinates = new_node(node_tree, ShaderNodeTexCoord)

    figure_mapping = new_node(node_tree, ShaderNodeMapping)
    set_vector_input(figure_mapping, "Scale", (1.0, 1.0, config.figure_stretch))
    link_nodes(node_tree, source=(coordinates, "Object"), target=(figure_mapping, "Vector"))
    figure = new_node(node_tree, ShaderNodeTexNoise)
    set_float_input(figure, "Scale", config.figure_scale)
    set_float_input(figure, "Detail", config.figure_detail)
    link_nodes(node_tree, source=(figure_mapping, "Vector"), target=(figure, "Vector"))
    figure_strength = new_math_node(node_tree, "MULTIPLY", operand=config.figure_strength)
    link_nodes(node_tree, source=(figure, "Fac"), target=(figure_strength, "Value"))
    board = new_color_mix_node(node_tree, a=linear_rgba(palette.wood), b=linear_rgba(palette.wood_light))
    link_sockets(node_tree, output_socket(figure_strength, "Value"), input_by_identifier(board, MIX_FACTOR))

    grain_mapping = new_node(node_tree, ShaderNodeMapping)
    set_vector_input(grain_mapping, "Scale", (1.0, 1.0, config.stretch))
    link_nodes(node_tree, source=(coordinates, "Object"), target=(grain_mapping, "Vector"))
    grain_wave = new_node(node_tree, ShaderNodeTexWave)
    grain_wave.wave_type = "BANDS"
    grain_wave.bands_direction = "X"
    set_float_input(grain_wave, "Scale", config.ring_scale)
    set_float_input(grain_wave, "Distortion", config.distortion)
    set_float_input(grain_wave, "Detail", config.ring_detail)
    set_float_input(grain_wave, "Detail Roughness", config.detail_roughness)
    link_nodes(node_tree, source=(grain_mapping, "Vector"), target=(grain_wave, "Vector"))
    grain_strength = new_math_node(node_tree, "MULTIPLY", operand=config.grain_contrast)
    link_nodes(node_tree, source=(grain_wave, "Fac"), target=(grain_strength, "Value"))
    grained = new_color_mix_node(node_tree, a=None, b=linear_rgba(palette.wood_dark))
    link_sockets(node_tree, output_by_identifier(board, MIX_RESULT), input_by_identifier(grained, MIX_A))
    link_sockets(node_tree, output_socket(grain_strength, "Value"), input_by_identifier(grained, MIX_FACTOR))

    tone = new_node(node_tree, ShaderNodeTexNoise)
    set_float_input(tone, "Scale", config.tone_scale)
    set_float_input(tone, "Detail", config.tone_detail)
    link_nodes(node_tree, source=(coordinates, "Object"), target=(tone, "Vector"))
    tone_strength = new_math_node(node_tree, "MULTIPLY", operand=config.tone_strength)
    link_nodes(node_tree, source=(tone, "Fac"), target=(tone_strength, "Value"))
    toned = new_color_mix_node(node_tree, a=None, b=linear_rgba(palette.wood_dark))
    link_sockets(node_tree, output_by_identifier(grained, MIX_RESULT), input_by_identifier(toned, MIX_A))
    link_sockets(node_tree, output_socket(tone_strength, "Value"), input_by_identifier(toned, MIX_FACTOR))
    link_sockets(node_tree, output_by_identifier(toned, MIX_RESULT), input_socket(principled, "Base Color"))

    _link_grain_surface(node_tree, principled, grain_wave=grain_wave, grain_mapping=grain_mapping, config=config)
    return material


def _link_grain_surface(
    node_tree: NodeTree,
    principled: ShaderNodeBsdfPrincipled,
    *,
    grain_wave: ShaderNodeTexWave,
    grain_mapping: ShaderNodeMapping,
    config: WoodConfig,
) -> None:
    """Drive roughness and the bump normal from the grain.

    The latewood lines read a touch glossier so the sun's highlight travels the
    grain, and those same lines plus a fine grain-aligned pore noise perturb the
    normal, giving the plank worked-timber relief that survives the dim glancing
    light instead of reading as a smooth crowned gradient.
    """
    gloss = new_math_node(node_tree, "MULTIPLY", operand=-config.roughness_variation)
    link_nodes(node_tree, source=(grain_wave, "Fac"), target=(gloss, "Value"))
    roughness = new_math_node(node_tree, "ADD", operand=config.roughness)
    link_nodes(node_tree, source=(gloss, "Value"), target=(roughness, "Value"))
    link_sockets(node_tree, output_socket(roughness, "Value"), input_socket(principled, "Roughness"))

    pore = new_node(node_tree, ShaderNodeTexNoise)
    set_float_input(pore, "Scale", config.pore_scale)
    set_float_input(pore, "Detail", config.pore_detail)
    link_nodes(node_tree, source=(grain_mapping, "Vector"), target=(pore, "Vector"))
    pore_strength = new_math_node(node_tree, "MULTIPLY", operand=config.pore_strength)
    link_nodes(node_tree, source=(pore, "Fac"), target=(pore_strength, "Value"))
    relief = new_math_node(node_tree, "ADD", operand=None)
    link_nodes(node_tree, source=(grain_wave, "Fac"), target=(relief, "Value"))
    link_sockets(node_tree, output_socket(pore_strength, "Value"), input_socket_at(relief, 1))

    bump = new_node(node_tree, ShaderNodeBump)
    set_float_input(bump, "Strength", config.bump_strength)
    link_sockets(node_tree, output_socket(relief, "Value"), input_socket(bump, "Height"))
    link_nodes(node_tree, source=(bump, "Normal"), target=(principled, "Normal"))
