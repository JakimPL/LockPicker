from enum import StrEnum
from typing import List, NamedTuple, Tuple, Type

from pydantic import BaseModel, ConfigDict
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from lockpicker.paths import CONFIG_FILE


class Color(NamedTuple):
    r: int
    g: int
    b: int


class PickShape(StrEnum):
    DIAMOND = "diamond"
    CIRCLE = "circle"


class RendererMode(StrEnum):
    FLAT = "flat"
    STYLED = "styled"


class Section(BaseModel):
    model_config = ConfigDict(frozen=True)


class ScreenConfig(Section):
    width: int
    height: int


class LayoutConfig(Section):
    x_offset: int
    bar_width: int
    bar_offset: int
    bar_y_offset: int


class PickConfig(Section):
    size: int
    offset: int
    width: int
    idle_offset: int
    discrepancy: int
    shapes: List[PickShape]


class ArrowConfig(Section):
    size: int
    width: int


class ColorConfig(Section):
    highlight: Color
    background: Color
    post_release: Color
    arrow: Color
    tumblers: List[Color]
    picks: List[Color]


class AlphaConfig(Section):
    opaque: int
    dimmed: int
    faint: int
    jam_divisor: int


class AnimationConfig(Section):
    speed: float
    fps: int


class RulesConfig(Section):
    default_number_of_picks: int
    default_max_height: int
    min_number_of_picks: int
    min_max_height: int


class SimulationConfig(Section):
    games: int
    max_moves: int


class ThemeConfig(Section):
    mode: RendererMode
    name: str
    directory: str
    highlight_tint: Color
    jam_tint: Color
    shadow_alpha: int
    badge_alpha: int


class Settings(BaseSettings):
    model_config = SettingsConfigDict(yaml_file=CONFIG_FILE, frozen=True)

    screen: ScreenConfig
    layout: LayoutConfig
    pick: PickConfig
    arrow: ArrowConfig
    color: ColorConfig
    alpha: AlphaConfig
    animation: AnimationConfig
    rules: RulesConfig
    simulation: SimulationConfig
    theme: ThemeConfig

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (YamlConfigSettingsSource(settings_cls),)


settings = Settings()
