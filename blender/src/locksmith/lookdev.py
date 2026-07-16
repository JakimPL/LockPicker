from bpy.types import Collection

from locksmith.blender.objects import linked_copy, override_slot_material
from locksmith.board import BoardGeometry
from locksmith.config.models.lookdev.lookdev import LookdevConfig
from locksmith.config.models.lookdev.tumbler import TumblerPlacement
from locksmith.shading.library import MaterialLibrary
from locksmith.staging import Prototypes
from locksmith.types import TumblerState


def build_lookdev(
    *,
    config: LookdevConfig,
    badge_tip_offset_pixels: float,
    prototypes: Prototypes,
    library: MaterialLibrary,
    board: BoardGeometry,
    collection: Collection,
) -> None:
    """Arrange the mock level for review stills: pins, badges, and both picks.

    The badge offset comes from the assets config so the still previews the
    exact placement rule the manifest publishes to the runtime.
    """
    for placement in config.tumblers:
        _place_tumbler(
            placement,
            badge_tip_offset_pixels=badge_tip_offset_pixels,
            prototypes=prototypes,
            library=library,
            board=board,
            collection=collection,
        )

    hovered = hovered_tumbler(config)
    engaged_x = board.column_center_x(hovered.position)
    tip = board.tip_z(upper=hovered.upper, height=hovered.height)
    bite = board.units(config.engaged_pick.bite_pixels)
    engaged_z = tip - bite if hovered.upper else tip + bite
    linked_copy(
        prototypes.pick_diamond,
        "pick_engaged",
        location=(engaged_x, config.engaged_pick.y, engaged_z),
        collection=collection,
    )
    linked_copy(
        prototypes.pick_circle,
        "pick_idle",
        location=(board.x_at(config.idle_pick.x_pixels), config.idle_pick.y, board.units(config.idle_pick.z_pixels)),
        collection=collection,
    )


def _place_tumbler(
    placement: TumblerPlacement,
    *,
    badge_tip_offset_pixels: float,
    prototypes: Prototypes,
    library: MaterialLibrary,
    board: BoardGeometry,
    collection: Collection,
) -> None:
    x = board.column_center_x(placement.position)
    tip = board.tip_z(upper=placement.upper, height=placement.height)
    prototype = prototypes.tumbler_upper if placement.upper else prototypes.tumbler_lower
    suffix = "u" if placement.upper else "l"
    pin = linked_copy(prototype, f"pin_{placement.position}_{suffix}", location=(x, 0.0, tip), collection=collection)
    override_slot_material(pin, slot=0, material=library.tumbler_material(metal=placement.metal, state=placement.state))
    if placement.state is TumblerState.MASTER:
        offset = board.units(badge_tip_offset_pixels)
        badge_z = tip + offset if placement.upper else tip - offset
        linked_copy(prototypes.badge, f"badge_{placement.position}", location=(x, 0.0, badge_z), collection=collection)


def hovered_tumbler(config: LookdevConfig) -> TumblerPlacement:
    """The tumbler the engaged pick presses on.

    Raises:
        LookupError: when the arrangement holds no hovered tumbler.
    """
    for placement in config.tumblers:
        if placement.state is TumblerState.HOVER:
            return placement
    raise LookupError("lookdev arrangement holds no hovered tumbler")
