from bpy.types import BooleanModifier, Object


def apply_boolean_difference(
    carrier: Object,
    *,
    name: str,
    cutter: Object,
) -> None:
    """Subtract the cutter from the carrier with the exact solver.

    The cutter stays in the file as a render-hidden wireframe so the cut
    remains editable.
    """
    modifier = carrier.modifiers.new(name, "BOOLEAN")
    if not isinstance(modifier, BooleanModifier):
        raise TypeError(f"expected BooleanModifier, Blender created {type(modifier).__name__}")

    modifier.operation = "DIFFERENCE"
    modifier.object = cutter
    modifier.solver = "EXACT"
    cutter.hide_render = True
    cutter.display_type = "WIRE"
