from typing import Tuple

from bpy.types import (
    Material,
    Node,
    NodeTree,
    ShaderNodeBsdfPrincipled,
    ShaderNodeBump,
    ShaderNodeMapping,
    ShaderNodeMapRange,
    ShaderNodeSeparateXYZ,
    ShaderNodeTexCoord,
    ShaderNodeTexNoise,
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
from locksmith.colors import linear_rgba, mixed_linear
from locksmith.schema.models.palette.palette import PaletteConfig
from locksmith.schema.models.shading.pocket import PocketShading
from locksmith.schema.models.shading.raceway import RacewayShading


def _wire_lit_surface(
    node_tree: NodeTree,
    principled: ShaderNodeBsdfPrincipled,
    color_source: Node,
    *,
    metallic: float,
    roughness: float,
    specular: float,
    glow: float,
) -> None:
    """Drive both the lit response and a faint emission floor from one color chain.

    The suns and cast shadows carry the depth; the floor keeps the authored
    pattern readable inside fully shadowed recesses instead of letting them
    collapse to black.
    """
    set_float_input(principled, "Metallic", metallic)
    set_float_input(principled, "Roughness", roughness)
    set_float_input(principled, "Specular IOR Level", specular)
    set_float_input(principled, "Emission Strength", glow)
    link_sockets(node_tree, output_by_identifier(color_source, MIX_RESULT), input_socket(principled, "Base Color"))
    link_sockets(node_tree, output_by_identifier(color_source, MIX_RESULT), input_socket(principled, "Emission Color"))


def make_pocket_material(
    name: str, *, palette: PaletteConfig, config: PocketShading, half_height_units: float
) -> Material:
    """Machined bore steel for the column troughs, zoned by height.

    The trough geometry gives the recess its shading, so the color chain
    only splits the finish at the shear lines — pin-polished on the shell
    bands, duller across the chamber run — then works the surface: soft
    oil-stain mottle and vertical honing streaks with a matching bump so the
    marks catch the suns.
    """
    material, node_tree, principled = new_principled_material(name)
    coordinates = new_node(node_tree, ShaderNodeTexCoord)

    zone = _pocket_zone(node_tree, coordinates, palette=palette, config=config, half_height_units=half_height_units)
    stained = _stain_layer(node_tree, coordinates, zone, palette=palette, config=config)
    honed, streak_swing = _streak_layer(node_tree, coordinates, stained, palette=palette, config=config)

    bump = new_node(node_tree, ShaderNodeBump)
    set_float_input(bump, "Strength", config.bump_strength)
    link_nodes(node_tree, source=(streak_swing, "Result"), target=(bump, "Height"))
    link_nodes(node_tree, source=(bump, "Normal"), target=(principled, "Normal"))

    _wire_lit_surface(
        node_tree,
        principled,
        honed,
        metallic=config.metallic,
        roughness=config.roughness,
        specular=config.specular,
        glow=config.glow,
    )
    return material


def _noise_swing(node_tree: NodeTree, noise: ShaderNodeTexNoise, *, config: PocketShading) -> ShaderNodeMapRange:
    """Stretch fBm's mid-crowded Fac to a full 0..1 swing.

    Without it the layer strengths mostly shift the mean tone; with it they
    set the amplitude of visible variation.
    """
    swing = new_node(node_tree, ShaderNodeMapRange)
    set_float_input(swing, "From Min", config.noise_low)
    set_float_input(swing, "From Max", config.noise_high)
    link_nodes(node_tree, source=(noise, "Fac"), target=(swing, "Value"))
    return swing


def _pocket_zone(
    node_tree: NodeTree,
    coordinates: ShaderNodeTexCoord,
    *,
    palette: PaletteConfig,
    config: PocketShading,
    half_height_units: float,
) -> Node:
    """Split the finish at the shear lines: polished band, dull chamber."""
    separate = new_node(node_tree, ShaderNodeSeparateXYZ)
    link_nodes(node_tree, source=(coordinates, "Object"), target=(separate, "Vector"))
    edge_distance = new_math_node(node_tree, "ABSOLUTE", operand=None)
    link_nodes(node_tree, source=(separate, "Z"), target=(edge_distance, "Value"))
    boundary = half_height_units - config.offset_units
    zone_range = new_node(node_tree, ShaderNodeMapRange)
    set_float_input(zone_range, "From Min", boundary - config.feather)
    set_float_input(zone_range, "From Max", boundary + config.feather)
    link_nodes(node_tree, source=(edge_distance, "Value"), target=(zone_range, "Value"))

    steel = mixed_linear(linear_rgba(palette.plate), linear_rgba(palette.rim), config.cool_mix, gain=1.0)
    chamber = mixed_linear(linear_rgba(palette.plate_deep), steel, config.chamber_mix, gain=config.chamber_gain)
    band = mixed_linear(steel, linear_rgba(palette.rim), config.band_sheen_mix, gain=config.band_gain)
    zone = new_color_mix_node(node_tree, a=chamber, b=band)
    link_sockets(node_tree, output_socket(zone_range, "Result"), input_by_identifier(zone, MIX_FACTOR))
    return zone


def _stain_layer(
    node_tree: NodeTree,
    coordinates: ShaderNodeTexCoord,
    base: Node,
    *,
    palette: PaletteConfig,
    config: PocketShading,
) -> Node:
    """Darken broad soft patches toward the deep tone — old oil staining."""
    mottle = new_node(node_tree, ShaderNodeTexNoise)
    set_float_input(mottle, "Scale", config.mottle_scale)
    set_float_input(mottle, "Detail", config.mottle_detail)
    link_nodes(node_tree, source=(coordinates, "Object"), target=(mottle, "Vector"))
    swing = _noise_swing(node_tree, mottle, config=config)
    mottle_strength = new_math_node(node_tree, "MULTIPLY", operand=config.mottle_strength)
    link_nodes(node_tree, source=(swing, "Result"), target=(mottle_strength, "Value"))
    stained = new_color_mix_node(node_tree, a=None, b=linear_rgba(palette.plate_deep))
    link_sockets(node_tree, output_by_identifier(base, MIX_RESULT), input_by_identifier(stained, MIX_A))
    link_sockets(node_tree, output_socket(mottle_strength, "Value"), input_by_identifier(stained, MIX_FACTOR))
    return stained


def _streak_layer(
    node_tree: NodeTree,
    coordinates: ShaderNodeTexCoord,
    base: Node,
    *,
    palette: PaletteConfig,
    config: PocketShading,
) -> Tuple[Node, ShaderNodeMapRange]:
    """Vertical honing marks along the pin travel; the swing also feeds the bump."""
    mapping = new_node(node_tree, ShaderNodeMapping)
    set_vector_input(mapping, "Scale", config.streak_mapping_scale)
    link_nodes(node_tree, source=(coordinates, "Object"), target=(mapping, "Vector"))
    streaks = new_node(node_tree, ShaderNodeTexNoise)
    set_float_input(streaks, "Scale", config.streak_scale)
    set_float_input(streaks, "Detail", config.streak_detail)
    link_nodes(node_tree, source=(mapping, "Vector"), target=(streaks, "Vector"))
    swing = _noise_swing(node_tree, streaks, config=config)
    streak_strength = new_math_node(node_tree, "MULTIPLY", operand=config.streak_strength)
    link_nodes(node_tree, source=(swing, "Result"), target=(streak_strength, "Value"))
    worn = mixed_linear(
        linear_rgba(palette.plate), linear_rgba(palette.rim), config.streak_sheen_mix, gain=config.streak_gain
    )
    honed = new_color_mix_node(node_tree, a=None, b=worn)
    link_sockets(node_tree, output_by_identifier(base, MIX_RESULT), input_by_identifier(honed, MIX_A))
    link_sockets(node_tree, output_socket(streak_strength, "Value"), input_by_identifier(honed, MIX_FACTOR))
    return honed, swing


def make_raceway_material(name: str, *, palette: PaletteConfig, config: RacewayShading) -> Material:
    """Keyway raceway floor: darker than the chamber, brushed along the picks.

    Noise compressed vertically leaves horizontal wear streaks — tools slide
    through sideways — while the lit response lets the carved band edges
    shadow the bed for real recess depth.
    """
    material, node_tree, principled = new_principled_material(name)

    coordinates = new_node(node_tree, ShaderNodeTexCoord)
    mapping = new_node(node_tree, ShaderNodeMapping)
    set_vector_input(mapping, "Scale", config.streak_mapping_scale)
    link_nodes(node_tree, source=(coordinates, "Object"), target=(mapping, "Vector"))
    streaks = new_node(node_tree, ShaderNodeTexNoise)
    set_float_input(streaks, "Scale", config.noise_scale)
    set_float_input(streaks, "Detail", config.noise_detail)
    link_nodes(node_tree, source=(mapping, "Vector"), target=(streaks, "Vector"))
    streak_strength = new_math_node(node_tree, "MULTIPLY", operand=config.strength)
    link_nodes(node_tree, source=(streaks, "Fac"), target=(streak_strength, "Value"))

    deep = linear_rgba(palette.plate_deep)
    base = mixed_linear(
        mixed_linear(deep, linear_rgba(palette.plate), config.base_mix, gain=1.0),
        linear_rgba(palette.patina),
        config.patina_mix,
        gain=1.0,
    )
    worn = mixed_linear(linear_rgba(palette.plate), linear_rgba(palette.key), config.key_mix, gain=config.gain)
    floor = new_color_mix_node(node_tree, a=base, b=worn)
    link_sockets(node_tree, output_socket(streak_strength, "Value"), input_by_identifier(floor, MIX_FACTOR))
    _wire_lit_surface(
        node_tree,
        principled,
        floor,
        metallic=config.metallic,
        roughness=config.roughness,
        specular=config.specular,
        glow=config.glow,
    )
    return material
