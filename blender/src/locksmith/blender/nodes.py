from typing import Final, List, Literal, Optional, Tuple, Type, TypeVar, Union

from bpy.types import (
    ColorRamp,
    ColorRampElement,
    Material,
    Node,
    NodeSocket,
    NodeSocketColor,
    NodeSocketFloat,
    NodeSocketFloatFactor,
    NodeSocketFloatUnsigned,
    NodeSocketVector,
    NodeSocketVectorEuler,
    NodeSocketVectorTranslation,
    NodeSocketVectorXYZ,
    NodeTree,
    ShaderNodeMath,
    ShaderNodeMix,
    ShaderNodeValToRGB,
    World,
)

from locksmith.types import RGBAColor, Vec3

NodeT = TypeVar("NodeT", bound=Node)

MathOperation = Literal["ADD", "SUBTRACT", "MULTIPLY", "POWER"]

MIX_FACTOR: Final[str] = "Factor_Float"
MIX_A: Final[str] = "A_Color"
MIX_B: Final[str] = "B_Color"
MIX_RESULT: Final[str] = "Result_Color"

# The fake-bpy-module stubs declare every bpy collection with an inconsistent
# base order (bpy_prop before its subclass bpy_prop_collection), which hides
# the inherited indexing/iteration protocol from mypy. The shims below own the
# resulting ignores so the rest of the codebase stays ignore-free.


def input_socket(node: Node, input_name: str) -> NodeSocket:
    socket: NodeSocket = node.inputs[input_name]  # type: ignore[index]  # stub MRO quirk, see above
    return socket


def input_socket_at(node: Node, index: int) -> NodeSocket:
    socket: NodeSocket = node.inputs[index]  # type: ignore[index]  # stub MRO quirk, see above
    return socket


def output_socket(node: Node, output_name: str) -> NodeSocket:
    socket: NodeSocket = node.outputs[output_name]  # type: ignore[index]  # stub MRO quirk, see above
    return socket


def node_inputs(node: Node) -> List[NodeSocket]:
    sockets: List[NodeSocket] = list(node.inputs)  # type: ignore[call-overload]  # stub MRO quirk, see above
    return sockets


def node_outputs(node: Node) -> List[NodeSocket]:
    sockets: List[NodeSocket] = list(node.outputs)  # type: ignore[call-overload]  # stub MRO quirk, see above
    return sockets


def tree_nodes(node_tree: NodeTree) -> List[Node]:
    nodes: List[Node] = list(node_tree.nodes)  # type: ignore[call-overload]  # stub MRO quirk, see above
    return nodes


def input_by_identifier(node: Node, identifier: str) -> NodeSocket:
    """Fetch an input socket by its unique identifier.

    Nodes like Mix expose one input per data type under the same display
    name, so only the identifier addresses the intended socket.

    Raises:
        LookupError: if no input socket carries the identifier.
    """
    for socket in node_inputs(node):
        if socket.identifier == identifier:
            return socket
    raise LookupError(f"no input socket {identifier} on {node.name}")


def output_by_identifier(node: Node, identifier: str) -> NodeSocket:
    """Fetch an output socket by its unique identifier.

    Raises:
        LookupError: if no output socket carries the identifier.
    """
    for socket in node_outputs(node):
        if socket.identifier == identifier:
            return socket
    raise LookupError(f"no output socket {identifier} on {node.name}")


def require_node_tree(id_block: Union[Material, World]) -> NodeTree:
    """Return the node tree of a nodes-enabled material or world.

    Raises:
        ValueError: if `use_nodes` has not been enabled on the datablock.
    """
    node_tree = id_block.node_tree
    if node_tree is None:
        raise ValueError(f"{id_block.name} has no node tree; enable use_nodes first")

    return node_tree


def new_node(node_tree: NodeTree, node_type: Type[NodeT]) -> NodeT:
    """Create a node and return it as its concrete type.

    Built-in shader node classes use their class name as the `bl_idname`
    creation key, so the requested type doubles as the key and the isinstance
    check proves the created node matches it.
    """
    node = node_tree.nodes.new(node_type.__name__)
    if not isinstance(node, node_type):
        raise TypeError(f"expected {node_type.__name__}, Blender created {type(node).__name__}")

    return node


def find_node(node_tree: NodeTree, node_type: Type[NodeT]) -> NodeT:
    """Return the first node of the requested type in the tree.

    Raises:
        LookupError: if the tree holds no node of that type.
    """
    for node in tree_nodes(node_tree):
        if isinstance(node, node_type):
            return node
    raise LookupError(f"no {node_type.__name__} node in {node_tree.name}")


def remove_node(node_tree: NodeTree, node: Node) -> None:
    node_tree.nodes.remove(node)


def link_sockets(node_tree: NodeTree, source: NodeSocket, target: NodeSocket) -> None:
    node_tree.links.new(source, target)


def link_nodes(
    node_tree: NodeTree,
    *,
    source: Tuple[Node, str],
    target: Tuple[Node, str],
) -> None:
    """Connect a (node, output socket name) pair to a (node, input socket name) pair."""
    source_node, output_name = source
    target_node, input_name = target
    link_sockets(node_tree, output_socket(source_node, output_name), input_socket(target_node, input_name))


def set_float_input(node: Node, input_name: str, value: float) -> None:
    """Set a float-valued input socket by name.

    Raises:
        TypeError: if the named socket holds a value of another kind.
    """
    socket = input_socket(node, input_name)
    match socket:
        case NodeSocketFloat() | NodeSocketFloatFactor() | NodeSocketFloatUnsigned():
            socket.default_value = value
        case _:
            raise TypeError(f"socket {input_name} on {node.name} holds no float value")


def set_color_input(node: Node, input_name: str, color: RGBAColor) -> None:
    """Set a color-valued input socket by name.

    Raises:
        TypeError: if the named socket holds a value of another kind.
    """
    socket = input_socket(node, input_name)
    match socket:
        case NodeSocketColor():
            # The stubs type color arrays as a bare bpy_prop_array; at runtime
            # the property accepts a 4-float sequence.
            socket.default_value = color  # type: ignore[assignment]
        case _:
            raise TypeError(f"socket {input_name} on {node.name} holds no color value")


def set_vector_input(node: Node, input_name: str, value: Vec3) -> None:
    """Set a vector-valued input socket by name.

    Raises:
        TypeError: if the named socket holds a value of another kind.
    """
    socket = input_socket(node, input_name)
    match socket:
        case NodeSocketVector() | NodeSocketVectorTranslation() | NodeSocketVectorEuler() | NodeSocketVectorXYZ():
            socket.default_value = value
        case _:
            raise TypeError(f"socket {input_name} on {node.name} holds no vector value")


def new_math_node(node_tree: NodeTree, operation: MathOperation, *, operand: Optional[float]) -> ShaderNodeMath:
    """Math node; `operand` fills the second input when the chain links only the first."""
    node = new_node(node_tree, ShaderNodeMath)
    node.operation = operation
    if operand is not None:
        socket = input_socket_at(node, 1)
        if not isinstance(socket, NodeSocketFloat):
            raise TypeError(f"math node {node.name} holds no float second input")
        socket.default_value = operand
    return node


def new_color_mix_node(
    node_tree: NodeTree,
    *,
    a: Optional[RGBAColor],
    b: Optional[RGBAColor],
) -> ShaderNodeMix:
    """Clamped RGBA mix node; unset ends are meant to be linked by the caller."""
    node = new_node(node_tree, ShaderNodeMix)
    node.data_type = "RGBA"
    node.clamp_factor = True
    if a is not None:
        _set_socket_color(node, MIX_A, a)
    if b is not None:
        _set_socket_color(node, MIX_B, b)
    return node


def _set_socket_color(node: Node, identifier: str, color: RGBAColor) -> None:
    socket = input_by_identifier(node, identifier)
    if not isinstance(socket, NodeSocketColor):
        raise TypeError(f"socket {identifier} on {node.name} holds no color value")
    # The stubs type color arrays as a bare bpy_prop_array; at runtime the
    # property accepts a 4-float sequence.
    socket.default_value = color  # type: ignore[assignment]


def require_color_ramp(node: ShaderNodeValToRGB) -> ColorRamp:
    """Return the node's color ramp.

    Raises:
        ValueError: if the node carries no ramp.
    """
    ramp = node.color_ramp
    if ramp is None:
        raise ValueError(f"{node.name} has no color ramp")

    return ramp


def set_color_ramp_stop(
    ramp: ColorRamp,
    index: int,
    *,
    position: float,
    color: RGBAColor,
) -> None:
    """Place one of the ramp's existing color stops."""
    element: ColorRampElement = ramp.elements[index]  # type: ignore[index]  # stub MRO quirk, see above
    element.position = position
    element.color = color  # type: ignore[assignment]  # stub types color arrays as bare bpy_prop_array


def set_color_ramp_positions(ramp: ColorRamp, *, start: float, end: float) -> None:
    """Place the ramp's two existing stops, keeping their colors."""
    first: ColorRampElement = ramp.elements[0]  # type: ignore[index]  # stub MRO quirk, see above
    second: ColorRampElement = ramp.elements[1]  # type: ignore[index]  # stub MRO quirk, see above
    first.position = start
    second.position = end


def add_color_ramp_stop(ramp: ColorRamp, *, position: float, color: RGBAColor) -> None:
    """Add a new color stop to the ramp at a position.

    The ramp keeps its stops sorted by position, so the new stop slots in
    wherever `position` places it without disturbing the others' colors.
    """
    element = ramp.elements.new(position)
    element.color = color  # type: ignore[assignment]  # stub types color arrays as bare bpy_prop_array
