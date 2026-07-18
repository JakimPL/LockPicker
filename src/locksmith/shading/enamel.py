from bpy.types import Material

from locksmith.blender.materials import new_principled_material
from locksmith.blender.nodes import set_color_input, set_float_input
from locksmith.colors import linear_rgba
from locksmith.schema.models.shading.enamel import EnamelConfig
from locksmith.types import HexColor


def make_enamel_material(name: str, *, color: HexColor, config: EnamelConfig) -> Material:
    """Glossy coated inlay; the clear coat gives the fired-enamel depth."""
    material, _node_tree, principled = new_principled_material(name)
    set_color_input(principled, "Base Color", linear_rgba(color))
    set_float_input(principled, "Roughness", config.roughness)
    set_float_input(principled, "Coat Weight", config.coat_weight)
    set_float_input(principled, "Coat Roughness", config.coat_roughness)
    return material
