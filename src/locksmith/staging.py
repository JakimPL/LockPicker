from dataclasses import dataclass

from bpy.types import Object
from mathutils import Vector

from locksmith.board import BoardGeometry
from locksmith.parts.badge import build_badge
from locksmith.parts.pick import build_pick
from locksmith.parts.pin import build_pin
from locksmith.scene_collections import SceneCollections
from locksmith.schema.models.anatomy.anatomy import AnatomyConfig
from locksmith.schema.models.staging import StagingConfig
from locksmith.shading.library import MaterialLibrary
from locksmith.types import Metal, PickShape


@dataclass(frozen=True)
class Prototypes:
    """Master objects the sprite cameras frame; scene placements copy these."""

    tumbler_upper: Object
    tumbler_lower: Object
    pick_diamond: Object
    pick_circle: Object
    badge: Object


def build_prototypes(
    *,
    board: BoardGeometry,
    anatomy: AnatomyConfig,
    library: MaterialLibrary,
    staging: StagingConfig,
    collections: SceneCollections,
) -> Prototypes:
    """Build one master of each renderable asset, parked left of the board.

    Prototypes stay out of renders; look-dev and the batch pipeline place
    render-enabled copies that share the prototype meshes.
    """
    tumbler_upper = build_pin(
        "tumbler_upper",
        upper=True,
        board=board,
        anatomy=anatomy.pin,
        material=library.tumblers[Metal.STEEL],
        collection=collections.tumbler_upper,
    )
    tumbler_upper.location = Vector((staging.tumbler_upper_x, 0.0, -board.height / 2))
    tumbler_lower = build_pin(
        "tumbler_lower",
        upper=False,
        board=board,
        anatomy=anatomy.pin,
        material=library.tumblers[Metal.STEEL],
        collection=collections.tumbler_lower,
    )
    tumbler_lower.location = Vector((staging.tumbler_lower_x, 0.0, board.height / 2))

    pick_diamond = build_pick(
        "pick_diamond",
        shape=PickShape.DIAMOND,
        board=board,
        anatomy=anatomy.pick,
        shaft_material=library.pick,
        ferrule_material=library.ferrule,
        grip_material=library.grips[PickShape.DIAMOND],
        collection=collections.pick_diamond,
    )
    pick_diamond.location = Vector((staging.pick_x, 0.0, staging.pick_diamond_z))
    pick_circle = build_pick(
        "pick_circle",
        shape=PickShape.CIRCLE,
        board=board,
        anatomy=anatomy.pick,
        shaft_material=library.pick,
        ferrule_material=library.ferrule,
        grip_material=library.grips[PickShape.CIRCLE],
        collection=collections.pick_circle,
    )
    pick_circle.location = Vector((staging.pick_x, 0.0, staging.pick_circle_z))

    badge = build_badge(
        anatomy=anatomy.badge,
        ring_material=library.rosette,
        inlay_material=library.enamel,
        collection=collections.badge,
    )
    badge.location = Vector((staging.badge_x, 0.0, staging.badge_z))

    prototypes = Prototypes(
        tumbler_upper=tumbler_upper,
        tumbler_lower=tumbler_lower,
        pick_diamond=pick_diamond,
        pick_circle=pick_circle,
        badge=badge,
    )
    for prototype in (tumbler_upper, tumbler_lower, pick_diamond, pick_circle, badge):
        prototype.hide_render = True
    return prototypes
