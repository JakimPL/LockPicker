from bpy.types import Material

from locksmith.blender.materials import new_principled_material
from locksmith.blender.nodes import set_color_input, set_float_input
from locksmith.colors import linear_rgba
from locksmith.config.models.shading.bore import BoreConfig
from locksmith.shading.effects import apply_roughness_breakup
from locksmith.types import HexColor


def make_bore_material(name: str, *, color: HexColor, config: BoreConfig) -> Material:
    """Near-black diffuse iron; low specular keeps the key sun out of the channel voids."""
    material, node_tree, principled = new_principled_material(name)
    set_float_input(principled, "Specular IOR Level", config.specular)
    set_color_input(principled, "Base Color", linear_rgba(color))
    apply_roughness_breakup(node_tree, principled, roughness=config.roughness, config=config.breakup)
    return material
