from typing import Final, Optional

from bpy.types import Material

from locksmith.blender.materials import new_principled_material
from locksmith.blender.nodes import (
    MIX_A,
    MIX_RESULT,
    input_by_identifier,
    input_socket,
    link_sockets,
    output_by_identifier,
    set_float_input,
)
from locksmith.colors import linear_rgba, multiplied
from locksmith.schema.models.shading.metals import MetalsConfig
from locksmith.shading.effects import (
    add_edge_wear,
    add_patina,
    apply_bevel_normal,
    apply_hover_glow,
    apply_roughness_breakup,
)
from locksmith.types import HexColor

_FULL_METALLIC: Final[float] = 1.0


def make_metal_material(
    name: str,
    *,
    base: HexColor,
    highlight: HexColor,
    roughness: float,
    config: MetalsConfig,
    verdigris: Optional[HexColor],
    hover: Optional[HexColor],
    jam: Optional[HexColor],
) -> Material:
    """Machined metal: roughness breakup, shader-bevel glints, and worn-bright edges.

    A jam color pre-multiplies the palette in sRGB byte space and dulls the
    finish, mirroring the runtime multiply blend the game applies to sprites.
    """
    if jam is not None:
        base = multiplied(base, jam)
        highlight = multiplied(highlight, jam)
        roughness = min(roughness + config.jam.roughness_shift, config.jam.roughness_cap)

    base_color = linear_rgba(base)
    highlight_color = linear_rgba(highlight)

    material, node_tree, principled = new_principled_material(name)
    set_float_input(principled, "Metallic", _FULL_METALLIC)
    apply_roughness_breakup(node_tree, principled, roughness=roughness, config=config.breakup)
    apply_bevel_normal(node_tree, principled, config=config.bevel_normal)
    wear = add_edge_wear(node_tree, base=base_color, highlight=highlight_color, config=config.edge_wear)
    if verdigris is not None:
        patina = add_patina(node_tree, base=base_color, verdigris=linear_rgba(verdigris), config=config.patina)
        link_sockets(node_tree, output_by_identifier(patina, MIX_RESULT), input_by_identifier(wear, MIX_A))

    link_sockets(node_tree, output_by_identifier(wear, MIX_RESULT), input_socket(principled, "Base Color"))
    if hover is not None:
        apply_hover_glow(node_tree, principled, color=linear_rgba(hover), config=config.hover)

    return material
