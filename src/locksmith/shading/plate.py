from bpy.types import (
    Material,
    NodeTree,
    ShaderNodeMapping,
    ShaderNodeMapRange,
    ShaderNodeMix,
    ShaderNodeNewGeometry,
    ShaderNodeSeparateXYZ,
    ShaderNodeTexCoord,
    ShaderNodeTexGradient,
    ShaderNodeTexNoise,
    ShaderNodeValToRGB,
)

from locksmith.blender.materials import new_emission_material
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
    require_color_ramp,
    set_color_ramp_positions,
    set_float_input,
    set_vector_input,
)
from locksmith.colors import linear_rgba, mixed_linear
from locksmith.schema.models.palette.palette import PaletteConfig
from locksmith.schema.models.shading.plate.plate import PlateShading
from locksmith.types import RGBAColor


def make_plate_material(
    name: str, *, palette: PaletteConfig, config: PlateShading, half_height_units: float
) -> Material:
    """Self-lit housing plate: mottled iron, rim glints, lamp pool, shell band, and depth fade.

    Painting the values into an emission surface keeps the plate at exact
    palette levels under any light rig while it still blocks light for the
    pin shadows; the depth fade sends slot interiors near-black. The shell
    band brightens the first height unit at both board edges — the region a
    seated pin retracts into — using |Z| so both edges match.
    """
    base = linear_rgba(palette.plate)
    dark = linear_rgba(palette.plate_dark)
    key = linear_rgba(palette.key)

    material, node_tree, emission = new_emission_material(name)
    set_float_input(emission, "Strength", config.emission_strength)

    mottle = new_node(node_tree, ShaderNodeTexNoise)
    set_float_input(mottle, "Scale", config.mottle.scale)
    set_float_input(mottle, "Detail", config.mottle.detail)
    darkened = new_color_mix_node(node_tree, a=base, b=dark)
    link_sockets(node_tree, output_socket(mottle, "Fac"), input_by_identifier(darkened, MIX_FACTOR))

    geometry = new_node(node_tree, ShaderNodeNewGeometry)
    rim_ramp = new_node(node_tree, ShaderNodeValToRGB)
    set_color_ramp_positions(require_color_ramp(rim_ramp), start=config.rim.start, end=config.rim.end)
    link_nodes(node_tree, source=(geometry, "Pointiness"), target=(rim_ramp, "Fac"))
    rim_strength = new_math_node(node_tree, "MULTIPLY", operand=config.rim.strength)
    link_nodes(node_tree, source=(rim_ramp, "Color"), target=(rim_strength, "Value"))
    rim = new_color_mix_node(node_tree, a=None, b=mixed_linear(base, key, config.rim.key_mix, gain=config.rim.gain))
    link_sockets(node_tree, output_by_identifier(darkened, MIX_RESULT), input_by_identifier(rim, MIX_A))
    link_sockets(node_tree, output_socket(rim_strength, "Value"), input_by_identifier(rim, MIX_FACTOR))

    coordinates = new_node(node_tree, ShaderNodeTexCoord)
    pool_mapping = new_node(node_tree, ShaderNodeMapping)
    set_vector_input(pool_mapping, "Location", config.pool.location)
    set_vector_input(pool_mapping, "Scale", (config.pool.scale, config.pool.scale, config.pool.scale))
    link_nodes(node_tree, source=(coordinates, "Object"), target=(pool_mapping, "Vector"))
    pool_gradient = new_node(node_tree, ShaderNodeTexGradient)
    pool_gradient.gradient_type = "SPHERICAL"
    link_nodes(node_tree, source=(pool_mapping, "Vector"), target=(pool_gradient, "Vector"))
    pool_strength = new_math_node(node_tree, "MULTIPLY", operand=config.pool.strength)
    link_nodes(node_tree, source=(pool_gradient, "Fac"), target=(pool_strength, "Value"))
    pool = new_color_mix_node(node_tree, a=None, b=mixed_linear(base, key, config.pool.key_mix, gain=config.pool.gain))
    link_sockets(node_tree, output_by_identifier(rim, MIX_RESULT), input_by_identifier(pool, MIX_A))
    link_sockets(node_tree, output_socket(pool_strength, "Value"), input_by_identifier(pool, MIX_FACTOR))

    separate = new_node(node_tree, ShaderNodeSeparateXYZ)
    link_nodes(node_tree, source=(coordinates, "Object"), target=(separate, "Vector"))
    fade_range = new_node(node_tree, ShaderNodeMapRange)
    set_float_input(fade_range, "From Min", config.depth_fade.near_y)
    set_float_input(fade_range, "From Max", config.depth_fade.far_y)
    link_nodes(node_tree, source=(separate, "Y"), target=(fade_range, "Value"))
    deep = new_color_mix_node(node_tree, a=None, b=linear_rgba(palette.plate_deep))
    link_sockets(node_tree, output_by_identifier(pool, MIX_RESULT), input_by_identifier(deep, MIX_A))
    link_sockets(node_tree, output_socket(fade_range, "Result"), input_by_identifier(deep, MIX_FACTOR))

    shell = _shell_band_mix(
        node_tree, separate=separate, base=base, key=key, config=config, half_height_units=half_height_units
    )
    link_sockets(node_tree, output_by_identifier(deep, MIX_RESULT), input_by_identifier(shell, MIX_A))

    link_sockets(node_tree, output_by_identifier(shell, MIX_RESULT), input_socket(emission, "Color"))
    return material


def _shell_band_mix(
    node_tree: NodeTree,
    *,
    separate: ShaderNodeSeparateXYZ,
    base: RGBAColor,
    key: RGBAColor,
    config: PlateShading,
    half_height_units: float,
) -> ShaderNodeMix:
    """Mix node brightening the first height unit at both board edges.

    The band mixes after the depth fade: the recessed rails between slots are
    deep-faded near-black, and a band mixed before the fade vanishes with
    them — the polished shell face must read across the whole board width.
    |Z| distance drives the band so both edges match.
    """
    edge_distance = new_math_node(node_tree, "ABSOLUTE", operand=None)
    link_nodes(node_tree, source=(separate, "Z"), target=(edge_distance, "Value"))
    shell_range = new_node(node_tree, ShaderNodeMapRange)
    set_float_input(shell_range, "From Min", half_height_units - config.shell.offset_units - config.shell.feather)
    set_float_input(shell_range, "From Max", half_height_units - config.shell.offset_units)
    link_nodes(node_tree, source=(edge_distance, "Value"), target=(shell_range, "Value"))
    shell_strength = new_math_node(node_tree, "MULTIPLY", operand=config.shell.strength)
    link_nodes(node_tree, source=(shell_range, "Result"), target=(shell_strength, "Value"))
    shell = new_color_mix_node(
        node_tree, a=None, b=mixed_linear(base, key, config.shell.key_mix, gain=config.shell.gain)
    )
    link_sockets(node_tree, output_socket(shell_strength, "Value"), input_by_identifier(shell, MIX_FACTOR))
    return shell
