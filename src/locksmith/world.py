from typing import Final, Tuple

from bpy.types import Scene, ShaderNodeMapRange, ShaderNodeSeparateXYZ, ShaderNodeTexCoord, ShaderNodeValToRGB

from locksmith.blender.nodes import (
    add_color_ramp_stop,
    input_socket_at,
    link_nodes,
    link_sockets,
    new_math_node,
    new_node,
    output_socket,
    require_color_ramp,
    set_color_ramp_stop,
    set_float_input,
)
from locksmith.blender.worlds import new_world
from locksmith.colors import WHITE, linear_rgba, mixed_linear
from locksmith.schema.models.palette.palette import PaletteConfig
from locksmith.schema.models.world import WorldConfig

_WORLD_NAME: Final[str] = "workshop"
_GRADIENT_DOMAIN: Final[Tuple[float, float]] = (-1.0, 1.0)


def build_world(scene: Scene, *, palette: PaletteConfig, config: WorldConfig) -> None:
    """Directional gradient environment: dark floor, cool mid, warm bright top-left.

    Curved metal shoulders sweep across this gradient under the orthographic
    camera, which is what makes them read as machined metal; a uniform
    environment leaves flat faces dead.
    """
    world, node_tree, background = new_world(_WORLD_NAME)

    coordinates = new_node(node_tree, ShaderNodeTexCoord)
    separate = new_node(node_tree, ShaderNodeSeparateXYZ)
    link_nodes(node_tree, source=(coordinates, "Generated"), target=(separate, "Vector"))
    z_term = new_math_node(node_tree, "MULTIPLY", operand=config.z_factor)
    link_nodes(node_tree, source=(separate, "Z"), target=(z_term, "Value"))
    x_term = new_math_node(node_tree, "MULTIPLY", operand=config.x_factor)
    link_nodes(node_tree, source=(separate, "X"), target=(x_term, "Value"))
    combined = new_math_node(node_tree, "ADD", operand=None)
    link_nodes(node_tree, source=(z_term, "Value"), target=(combined, "Value"))
    link_sockets(node_tree, output_socket(x_term, "Value"), input_socket_at(combined, 1))

    normalized = new_node(node_tree, ShaderNodeMapRange)
    domain_start, domain_end = _GRADIENT_DOMAIN
    set_float_input(normalized, "From Min", domain_start)
    set_float_input(normalized, "From Max", domain_end)
    link_nodes(node_tree, source=(combined, "Value"), target=(normalized, "Value"))

    ramp = new_node(node_tree, ShaderNodeValToRGB)
    color_ramp = require_color_ramp(ramp)
    set_color_ramp_stop(color_ramp, 0, position=0.0, color=linear_rgba(palette.world_floor))
    set_color_ramp_stop(
        color_ramp,
        1,
        position=1.0,
        color=mixed_linear(linear_rgba(palette.key), WHITE, config.top_white_mix, gain=config.top_gain),
    )
    add_color_ramp_stop(color_ramp, position=config.mid_position, color=linear_rgba(palette.world_mid))
    link_nodes(node_tree, source=(normalized, "Result"), target=(ramp, "Fac"))

    link_nodes(node_tree, source=(ramp, "Color"), target=(background, "Color"))
    set_float_input(background, "Strength", config.strength)
    scene.world = world
