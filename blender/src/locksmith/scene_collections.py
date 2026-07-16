from dataclasses import dataclass
from typing import Final

from bpy.types import Collection, Scene

from locksmith.blender.collections import new_child_collection

BACKGROUND_COLLECTION: Final[str] = "BG"
FRAME_COLLECTION: Final[str] = "FRAME"
TUMBLER_UPPER_COLLECTION: Final[str] = "TUMBLER_UPPER"
TUMBLER_LOWER_COLLECTION: Final[str] = "TUMBLER_LOWER"
PICK_DIAMOND_COLLECTION: Final[str] = "PICK_DIAMOND"
PICK_CIRCLE_COLLECTION: Final[str] = "PICK_CIRCLE"
BADGE_COLLECTION: Final[str] = "BADGE_MASTER"
SHADOW_CATCHER_COLLECTION: Final[str] = "SHADOWCATCHER"
RIG_COLLECTION: Final[str] = "RIG"
LOOKDEV_COLLECTION: Final[str] = "LOOKDEV"


@dataclass(frozen=True)
class SceneCollections:
    """One collection per sprite pass plus the rig and the look-dev arrangement.

    The batch renderer isolates each sprite pass by toggling these
    collections, so every renderable asset owns exactly one of them.
    """

    background: Collection
    frame: Collection
    tumbler_upper: Collection
    tumbler_lower: Collection
    pick_diamond: Collection
    pick_circle: Collection
    badge: Collection
    shadow_catcher: Collection
    rig: Collection
    lookdev: Collection


def build_scene_collections(scene: Scene) -> SceneCollections:
    return SceneCollections(
        background=new_child_collection(scene, BACKGROUND_COLLECTION),
        frame=new_child_collection(scene, FRAME_COLLECTION),
        tumbler_upper=new_child_collection(scene, TUMBLER_UPPER_COLLECTION),
        tumbler_lower=new_child_collection(scene, TUMBLER_LOWER_COLLECTION),
        pick_diamond=new_child_collection(scene, PICK_DIAMOND_COLLECTION),
        pick_circle=new_child_collection(scene, PICK_CIRCLE_COLLECTION),
        badge=new_child_collection(scene, BADGE_COLLECTION),
        shadow_catcher=new_child_collection(scene, SHADOW_CATCHER_COLLECTION),
        rig=new_child_collection(scene, RIG_COLLECTION),
        lookdev=new_child_collection(scene, LOOKDEV_COLLECTION),
    )
