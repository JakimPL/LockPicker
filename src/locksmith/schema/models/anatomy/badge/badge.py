from locksmith.schema.models.anatomy.badge.inlay import InlayAnatomy
from locksmith.schema.models.anatomy.badge.ring import RingAnatomy
from locksmith.schema.models.base import SceneModel


class BadgeAnatomy(SceneModel):
    """Engraved rosette with an enamel inlay marking master tumblers."""

    ring: RingAnatomy
    inlay: InlayAnatomy
