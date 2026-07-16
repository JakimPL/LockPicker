from typing import Final

from bpy.types import (
    NodeTree,
    ShaderNodeBevel,
    ShaderNodeBsdfPrincipled,
    ShaderNodeLayerWeight,
    ShaderNodeMapping,
    ShaderNodeMapRange,
    ShaderNodeMix,
    ShaderNodeNewGeometry,
    ShaderNodeTexCoord,
    ShaderNodeTexNoise,
    ShaderNodeValToRGB,
)

from locksmith.blender.nodes import (
    MIX_FACTOR,
    input_by_identifier,
    input_socket_at,
    link_nodes,
    link_sockets,
    new_color_mix_node,
    new_math_node,
    new_node,
    output_socket,
    require_color_ramp,
    set_color_input,
    set_color_ramp_positions,
    set_color_ramp_stop,
    set_float_input,
    set_vector_input,
)
from locksmith.colors import BLACK, WHITE
from locksmith.config.models.shading.bevel_normal import BevelNormalConfig
from locksmith.config.models.shading.breakup import BreakupConfig
from locksmith.config.models.shading.edge_wear import EdgeWearConfig
from locksmith.config.models.shading.hover import HoverConfig
from locksmith.config.models.shading.patina import PatinaConfig
from locksmith.types import RGBAColor

_NOISE_MIDPOINT: Final[float] = 0.5


def apply_roughness_breakup(
    node_tree: NodeTree,
    principled: ShaderNodeBsdfPrincipled,
    *,
    roughness: float,
    config: BreakupConfig,
) -> None:
    noise = new_node(node_tree, ShaderNodeTexNoise)
    set_float_input(noise, "Scale", config.noise_scale)
    set_float_input(noise, "Detail", config.noise_detail)
    spread_range = new_node(node_tree, ShaderNodeMapRange)
    set_float_input(spread_range, "From Min", 0.0)
    set_float_input(spread_range, "From Max", 1.0)
    set_float_input(spread_range, "To Min", max(roughness - config.spread, config.minimum))
    set_float_input(spread_range, "To Max", min(roughness + config.spread, 1.0))
    link_nodes(node_tree, source=(noise, "Fac"), target=(spread_range, "Value"))

    coordinates = new_node(node_tree, ShaderNodeTexCoord)
    mapping = new_node(node_tree, ShaderNodeMapping)
    set_vector_input(mapping, "Scale", config.streak_mapping_scale)
    link_nodes(node_tree, source=(coordinates, "Object"), target=(mapping, "Vector"))
    streaks = new_node(node_tree, ShaderNodeTexNoise)
    set_float_input(streaks, "Scale", config.streak_scale)
    set_float_input(streaks, "Detail", config.streak_detail)
    link_nodes(node_tree, source=(mapping, "Vector"), target=(streaks, "Vector"))
    centered = new_math_node(node_tree, "SUBTRACT", operand=_NOISE_MIDPOINT)
    link_nodes(node_tree, source=(streaks, "Fac"), target=(centered, "Value"))
    strength = new_math_node(node_tree, "MULTIPLY", operand=config.strength)
    link_nodes(node_tree, source=(centered, "Value"), target=(strength, "Value"))

    total = new_math_node(node_tree, "ADD", operand=None)
    link_nodes(node_tree, source=(spread_range, "Result"), target=(total, "Value"))
    link_sockets(node_tree, output_socket(strength, "Value"), input_socket_at(total, 1))
    link_nodes(node_tree, source=(total, "Value"), target=(principled, "Roughness"))


def add_edge_wear(
    node_tree: NodeTree,
    *,
    base: RGBAColor,
    highlight: RGBAColor,
    config: EdgeWearConfig,
) -> ShaderNodeMix:
    """Mix node brightening convex edges toward the highlight; handled metal wears shiny."""
    geometry = new_node(node_tree, ShaderNodeNewGeometry)
    ramp = new_node(node_tree, ShaderNodeValToRGB)
    set_color_ramp_positions(require_color_ramp(ramp), start=config.start, end=config.end)
    link_nodes(node_tree, source=(geometry, "Pointiness"), target=(ramp, "Fac"))
    strength = new_math_node(node_tree, "MULTIPLY", operand=config.strength)
    link_nodes(node_tree, source=(ramp, "Color"), target=(strength, "Value"))
    wear = new_color_mix_node(node_tree, a=base, b=highlight)
    link_sockets(node_tree, output_socket(strength, "Value"), input_by_identifier(wear, MIX_FACTOR))
    return wear


def add_patina(
    node_tree: NodeTree,
    *,
    base: RGBAColor,
    verdigris: RGBAColor,
    config: PatinaConfig,
) -> ShaderNodeMix:
    """Mix node laying verdigris into concave crevices via an inverted pointiness ramp."""
    geometry = new_node(node_tree, ShaderNodeNewGeometry)
    ramp = new_node(node_tree, ShaderNodeValToRGB)
    color_ramp = require_color_ramp(ramp)
    set_color_ramp_stop(color_ramp, 0, position=config.start, color=WHITE)
    set_color_ramp_stop(color_ramp, 1, position=config.end, color=BLACK)
    link_nodes(node_tree, source=(geometry, "Pointiness"), target=(ramp, "Fac"))
    patina = new_color_mix_node(node_tree, a=base, b=verdigris)
    link_sockets(node_tree, output_socket(ramp, "Color"), input_by_identifier(patina, MIX_FACTOR))
    return patina


def apply_bevel_normal(
    node_tree: NodeTree,
    principled: ShaderNodeBsdfPrincipled,
    *,
    config: BevelNormalConfig,
) -> None:
    bevel = new_node(node_tree, ShaderNodeBevel)
    bevel.samples = config.samples
    set_float_input(bevel, "Radius", config.radius)
    link_nodes(node_tree, source=(bevel, "Normal"), target=(principled, "Normal"))


def apply_hover_glow(
    node_tree: NodeTree,
    principled: ShaderNodeBsdfPrincipled,
    *,
    color: RGBAColor,
    config: HoverConfig,
) -> None:
    """Facing-weighted emission rim; the pin reads as lit rather than recolored."""
    set_color_input(principled, "Emission Color", color)
    layer_weight = new_node(node_tree, ShaderNodeLayerWeight)
    set_float_input(layer_weight, "Blend", config.blend)
    facing_power = new_math_node(node_tree, "POWER", operand=config.power)
    link_nodes(node_tree, source=(layer_weight, "Facing"), target=(facing_power, "Value"))
    gain = new_math_node(node_tree, "MULTIPLY", operand=config.gain)
    link_nodes(node_tree, source=(facing_power, "Value"), target=(gain, "Value"))
    link_nodes(node_tree, source=(gain, "Value"), target=(principled, "Emission Strength"))
