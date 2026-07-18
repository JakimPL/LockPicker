from pydantic import BaseModel, ConfigDict


class SceneModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
