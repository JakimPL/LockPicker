from locksmith.schema.models.anatomy.background import BackgroundAnatomy
from locksmith.schema.models.anatomy.badge.badge import BadgeAnatomy
from locksmith.schema.models.anatomy.bench import BenchAnatomy
from locksmith.schema.models.anatomy.flange.flange import FlangeAnatomy
from locksmith.schema.models.anatomy.keyway.keyway import KeywayAnatomy
from locksmith.schema.models.anatomy.lip import LipAnatomy
from locksmith.schema.models.anatomy.pick.pick import PickAnatomy
from locksmith.schema.models.anatomy.pin.pin import PinAnatomy
from locksmith.schema.models.anatomy.plate import PlateAnatomy
from locksmith.schema.models.anatomy.screws.screws import ScrewsAnatomy
from locksmith.schema.models.anatomy.shadow_catcher import ShadowCatcherAnatomy
from locksmith.schema.models.base import SceneModel


class AnatomyConfig(SceneModel):
    pin: PinAnatomy
    plate: PlateAnatomy
    bench: BenchAnatomy
    keyway: KeywayAnatomy
    flange: FlangeAnatomy
    lip: LipAnatomy
    screws: ScrewsAnatomy
    background: BackgroundAnatomy
    pick: PickAnatomy
    badge: BadgeAnatomy
    shadow_catcher: ShadowCatcherAnatomy
