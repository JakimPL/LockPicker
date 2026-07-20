from typing import Tuple

import bpy
from bpy.types import (
    Material,
    NodeTree,
    ShaderNodeBsdfPrincipled,
    ShaderNodeEmission,
    ShaderNodeOutputMaterial,
)

from locksmith.blender.nodes import find_node, link_nodes, new_node, remove_node, require_node_tree


def new_principled_material(name: str) -> Tuple[Material, NodeTree, ShaderNodeBsdfPrincipled]:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    node_tree = require_node_tree(material)
    principled = find_node(node_tree, ShaderNodeBsdfPrincipled)
    return material, node_tree, principled


def new_emission_material(name: str) -> Tuple[Material, NodeTree, ShaderNodeEmission]:
    """Surface-emission material shell; the caller wires the emission color chain.

    Emission surfaces render at exact authored values regardless of lights
    while still blocking light, so they suit painted backdrops that must cast
    shadows.
    """
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    node_tree = require_node_tree(material)
    output = find_node(node_tree, ShaderNodeOutputMaterial)
    remove_node(node_tree, find_node(node_tree, ShaderNodeBsdfPrincipled))
    emission = new_node(node_tree, ShaderNodeEmission)
    link_nodes(node_tree, source=(emission, "Emission"), target=(output, "Surface"))
    return material, node_tree, emission
