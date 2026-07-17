from locksmith.config.models.anatomy.background import BackgroundAnatomy
from locksmith.config.models.anatomy.badge.badge import BadgeAnatomy
from locksmith.config.models.anatomy.bench import BenchAnatomy
from locksmith.config.models.anatomy.flange.flange import FlangeAnatomy
from locksmith.config.models.anatomy.keyway.keyway import KeywayAnatomy
from locksmith.config.models.anatomy.lip import LipAnatomy
from locksmith.config.models.anatomy.pick.pick import PickAnatomy
from locksmith.config.models.anatomy.pin.pin import PinAnatomy
from locksmith.config.models.anatomy.plate import PlateAnatomy
from locksmith.config.models.anatomy.screws.screws import ScrewsAnatomy
from locksmith.config.models.anatomy.shadow_catcher import ShadowCatcherAnatomy
from locksmith.config.models.base import SceneModel


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
