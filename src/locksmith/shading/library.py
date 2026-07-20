from dataclasses import dataclass
from typing import Dict, Optional

from bpy.types import Material

from locksmith.schema.models.palette.metal_colors import MetalColors
from locksmith.schema.models.palette.palette import PaletteConfig
from locksmith.schema.models.shading.metals import MetalsConfig
from locksmith.schema.models.shading.shading import ShadingConfig
from locksmith.shading.bore import make_bore_material
from locksmith.shading.enamel import make_enamel_material
from locksmith.shading.grip import make_grip_material
from locksmith.shading.metal import make_metal_material
from locksmith.shading.plate import make_plate_material
from locksmith.shading.recess import make_pocket_material, make_raceway_material
from locksmith.shading.wood import make_wood_material
from locksmith.types import HexColor, Metal, PickShape, TumblerState


@dataclass(frozen=True)
class MaterialLibrary:
    """Every material in the scene, created once and shared by the builders."""

    tumblers: Dict[Metal, Material]
    hovered: Dict[Metal, Material]
    jammed: Dict[Metal, Material]
    plate: Material
    plate_stage: Material
    wood: Material
    wood_carved: Material
    bore: Material
    pocket: Material
    raceway: Material
    enamel: Material
    rosette: Material
    lip: Material
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


@dataclass(frozen=True)
class _MetalRecipe:
    base: HexColor
    highlight: HexColor
    roughness: float
    verdigris: Optional[HexColor]


@dataclass(frozen=True)
class _TumblerVariant:
    suffix: str
    hover: Optional[HexColor]
    jam: Optional[HexColor]


def make_material_library(
    *,
    palette: PaletteConfig,
    shading: ShadingConfig,
    plate_half_height: float,
) -> MaterialLibrary:
    metals = shading.metals
    return MaterialLibrary(
        tumblers=_metal_variants(variant=_TumblerVariant("", None, None), palette=palette, metals=metals),
        hovered=_metal_variants(variant=_TumblerVariant("_hover", palette.hover, None), palette=palette, metals=metals),
        jammed=_metal_variants(variant=_TumblerVariant("_jam", None, palette.jam), palette=palette, metals=metals),
        plate=make_plate_material(
            "frame_plate",
            palette=palette,
            config=shading.plate,
            half_height_units=plate_half_height,
        ),
        plate_stage=make_plate_material(
            "sprite_stage_plate",
            palette=palette,
            config=shading.plate.model_copy(
                update={"shell": shading.plate.shell.model_copy(update={"strength": 0.0})},
            ),
            half_height_units=plate_half_height,
        ),
        wood=make_wood_material(
            "bench_wood",
            palette=palette,
            config=shading.wood,
        ),
        wood_carved=make_wood_material(
            "bench_wood_carved",
            palette=palette.model_copy(
                update={
                    "wood_light": palette.wood_dark,
                    "wood": palette.wood_deep,
                    "wood_dark": palette.wood_black,
                }
            ),
            config=shading.wood,
        ),
        bore=make_bore_material(
            "bore_iron",
            color=palette.bore,
            config=shading.bore,
        ),
        pocket=make_pocket_material(
            "pocket_bore",
            palette=palette,
            config=shading.pocket,
            half_height_units=plate_half_height,
        ),
        raceway=make_raceway_material(
            "raceway_floor",
            palette=palette,
            config=shading.raceway,
        ),
        enamel=make_enamel_material(
            "badge_enamel",
            color=palette.enamel,
            config=shading.enamel,
        ),
        rosette=_plain_metal(
            "badge_rosette",
            base=palette.rosette,
            highlight=palette.steel.base,
            roughness=metals.roughness.rosette,
            metals=metals,
        ),
        lip=_plain_metal(
            "lip_steel",
            base=palette.lip.base,
            highlight=palette.lip.highlight,
            roughness=metals.roughness.lip,
            metals=metals,
        ),
        pick=_plain_metal(
            "pick_steel",
            base=palette.pick.base,
            highlight=palette.pick.highlight,
            roughness=metals.roughness.pick,
            metals=metals,
        ),
        ferrule=_plain_metal(
            "pick_ferrule",
            base=palette.brass.base,
            highlight=palette.brass.highlight,
            roughness=metals.roughness.ferrule,
            metals=metals,
        ),
        grips={
            PickShape.DIAMOND: make_grip_material(
                "pick_grip_a",
                color=palette.grip_a,
                config=shading.grip,
            ),
            PickShape.CIRCLE: make_grip_material(
                "pick_grip_b",
                color=palette.grip_b,
                config=shading.grip,
            ),
        },
    )


def _metal_variants(
    *,
    variant: _TumblerVariant,
    palette: PaletteConfig,
    metals: MetalsConfig,
) -> Dict[Metal, Material]:
    return {metal: _tumbler_metal(metal, variant=variant, palette=palette, metals=metals) for metal in Metal}


def _tumbler_metal(
    metal: Metal,
    *,
    variant: _TumblerVariant,
    palette: PaletteConfig,
    metals: MetalsConfig,
) -> Material:
    recipe = _recipe_of(metal, palette=palette, metals=metals)
    return make_metal_material(
        f"pin_{metal.value}{variant.suffix}",
        base=recipe.base,
        highlight=recipe.highlight,
        roughness=recipe.roughness,
        config=metals,
        verdigris=recipe.verdigris,
        hover=variant.hover,
        jam=variant.jam,
    )


def _plain_metal(
    name: str,
    *,
    base: HexColor,
    highlight: HexColor,
    roughness: float,
    metals: MetalsConfig,
) -> Material:
    return make_metal_material(
        name,
        base=base,
        highlight=highlight,
        roughness=roughness,
        config=metals,
        verdigris=None,
        hover=None,
        jam=None,
    )


def _recipe_of(metal: Metal, *, palette: PaletteConfig, metals: MetalsConfig) -> _MetalRecipe:
    colors = _colors_of(metal, palette=palette)
    return _MetalRecipe(
        base=colors.base,
        highlight=colors.highlight,
        roughness=_roughness_of(metal, metals=metals),
        verdigris=palette.patina if metal is Metal.COPPER else None,
    )


def _colors_of(metal: Metal, *, palette: PaletteConfig) -> MetalColors:
    match metal:
        case Metal.STEEL:
            return palette.steel
        case Metal.BRASS:
            return palette.brass
        case Metal.COPPER:
            return palette.copper


def _roughness_of(metal: Metal, *, metals: MetalsConfig) -> float:
    match metal:
        case Metal.STEEL:
            return metals.roughness.steel
        case Metal.BRASS:
            return metals.roughness.brass
        case Metal.COPPER:
            return metals.roughness.copper
