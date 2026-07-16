from dataclasses import dataclass
from typing import Dict, Optional

from bpy.types import Material

from locksmith.config.models.palette.metal_colors import MetalColors
from locksmith.config.models.palette.palette import PaletteConfig
from locksmith.config.models.shading.shading import ShadingConfig
from locksmith.shading.bore import make_bore_material
from locksmith.shading.enamel import make_enamel_material
from locksmith.shading.grip import make_grip_material
from locksmith.shading.metal import make_metal_material
from locksmith.shading.plate import make_plate_material
from locksmith.shading.wood import make_wood_material
from locksmith.types import HexColor, Metal, PickShape, TumblerState


@dataclass(frozen=True)
class MaterialLibrary:
    """Every material in the scene, created once and shared by the builders."""

    tumblers: Dict[Metal, Material]
    hovered: Dict[Metal, Material]
    jammed: Dict[Metal, Material]
    plate: Material
    wood: Material
    bore: Material
    enamel: Material
    rosette: Material
    pick: Material
    ferrule: Material
    grips: Dict[PickShape, Material]

    def tumbler_material(self, *, metal: Metal, state: TumblerState) -> Material:
        match state:
            case TumblerState.HOVER:
                return self.hovered[metal]
            case TumblerState.JAM:
                return self.jammed[metal]
            case TumblerState.PLAIN | TumblerState.MASTER:
                return self.tumblers[metal]


def make_material_library(*, palette: PaletteConfig, shading: ShadingConfig) -> MaterialLibrary:
    metals = shading.metals

    def colors_of(metal: Metal) -> MetalColors:
        match metal:
            case Metal.STEEL:
                return palette.steel
            case Metal.BRASS:
                return palette.brass
            case Metal.COPPER:
                return palette.copper

    def roughness_of(metal: Metal) -> float:
        match metal:
            case Metal.STEEL:
                return metals.roughness.steel
            case Metal.BRASS:
                return metals.roughness.brass
            case Metal.COPPER:
                return metals.roughness.copper

    def verdigris_of(metal: Metal) -> Optional[HexColor]:
        return palette.patina if metal is Metal.COPPER else None

    tumblers = {
        metal: make_metal_material(
            f"pin_{metal.value}",
            base=colors_of(metal).base,
            highlight=colors_of(metal).highlight,
            roughness=roughness_of(metal),
            config=metals,
            verdigris=verdigris_of(metal),
            hover=None,
            jam=None,
        )
        for metal in Metal
    }
    hovered = {
        metal: make_metal_material(
            f"pin_{metal.value}_hover",
            base=colors_of(metal).base,
            highlight=colors_of(metal).highlight,
            roughness=roughness_of(metal),
            config=metals,
            verdigris=verdigris_of(metal),
            hover=palette.hover,
            jam=None,
        )
        for metal in Metal
    }
    jammed = {
        metal: make_metal_material(
            f"pin_{metal.value}_jam",
            base=colors_of(metal).base,
            highlight=colors_of(metal).highlight,
            roughness=roughness_of(metal),
            config=metals,
            verdigris=verdigris_of(metal),
            hover=None,
            jam=palette.jam,
        )
        for metal in Metal
    }
    return MaterialLibrary(
        tumblers=tumblers,
        hovered=hovered,
        jammed=jammed,
        plate=make_plate_material("frame_plate", palette=palette, config=shading.plate),
        wood=make_wood_material("bench_wood", palette=palette, config=shading.wood),
        bore=make_bore_material("bore_iron", color=palette.bore, config=shading.bore),
        enamel=make_enamel_material("badge_enamel", color=palette.enamel, config=shading.enamel),
        rosette=make_metal_material(
            "badge_rosette",
            base=palette.rosette,
            highlight=palette.steel.base,
            roughness=metals.roughness.rosette,
            config=metals,
            verdigris=None,
            hover=None,
            jam=None,
        ),
        pick=make_metal_material(
            "pick_steel",
            base=palette.pick.base,
            highlight=palette.pick.highlight,
            roughness=metals.roughness.pick,
            config=metals,
            verdigris=None,
            hover=None,
            jam=None,
        ),
        ferrule=make_metal_material(
            "pick_ferrule",
            base=palette.brass.base,
            highlight=palette.brass.highlight,
            roughness=metals.roughness.ferrule,
            config=metals,
            verdigris=None,
            hover=None,
            jam=None,
        ),
        grips={
            PickShape.DIAMOND: make_grip_material("pick_grip_a", color=palette.grip_a, config=shading.grip),
            PickShape.CIRCLE: make_grip_material("pick_grip_b", color=palette.grip_b, config=shading.grip),
        },
    )
