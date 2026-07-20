from typing import Tuple

import bpy
from bpy.types import NodeTree, ShaderNodeBackground, World

from locksmith.blender.nodes import find_node, require_node_tree


def new_world(name: str) -> Tuple[World, NodeTree, ShaderNodeBackground]:
    world = bpy.data.worlds.new(name)
    world.use_nodes = True
    node_tree = require_node_tree(world)
    background = find_node(node_tree, ShaderNodeBackground)
    return world, node_tree, background
