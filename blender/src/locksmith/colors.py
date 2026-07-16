from typing import Final, Tuple

from locksmith.types import HexColor, RGBAColor, RGBColor

WHITE: Final[RGBAColor] = (1.0, 1.0, 1.0, 1.0)
BLACK: Final[RGBAColor] = (0.0, 0.0, 0.0, 1.0)

_SRGB_LINEAR_THRESHOLD: Final[float] = 0.04045


def _linear_channel(byte: int) -> float:
    channel = byte / 255.0
    if channel <= _SRGB_LINEAR_THRESHOLD:
        return channel / 12.92
    return float(((channel + 0.055) / 1.055) ** 2.4)


def _bytes_of(code: HexColor) -> Tuple[int, int, int]:
    return (int(code[0:2], 16), int(code[2:4], 16), int(code[4:6], 16))


def linear_rgb(code: HexColor) -> RGBColor:
    red, green, blue = _bytes_of(code)
    return (_linear_channel(red), _linear_channel(green), _linear_channel(blue))


def linear_rgba(code: HexColor) -> RGBAColor:
    return (*linear_rgb(code), 1.0)


def scaled(code: HexColor, factor: float) -> HexColor:
    return "".join(f"{min(255, int(byte * factor)):02X}" for byte in _bytes_of(code))


def multiplied(code: HexColor, other: HexColor) -> HexColor:
    """Per-channel sRGB byte product; matches a runtime multiply blend over the sprite."""
    return "".join(f"{a * b // 255:02X}" for a, b in zip(_bytes_of(code), _bytes_of(other)))


def mixed_linear(start: RGBAColor, end: RGBAColor, factor: float, *, gain: float) -> RGBAColor:
    mixed = tuple(min(1.0, (start[i] + (end[i] - start[i]) * factor) * gain) for i in range(3))
    return (mixed[0], mixed[1], mixed[2], 1.0)
