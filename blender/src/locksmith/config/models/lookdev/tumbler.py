from locksmith.config.models.base import SceneModel
from locksmith.types import Metal, TumblerState


class TumblerPlacement(SceneModel):
    position: int
    upper: bool
    height: float
    metal: Metal
    state: TumblerState
