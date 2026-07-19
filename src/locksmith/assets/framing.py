import math
from dataclasses import dataclass
from typing import Tuple

from locksmith.types import PixelPair, Vec3

Bounds = Tuple[Vec3, Vec3]


@dataclass(frozen=True)
class SpriteFraming:
    """Sprite canvas in whole logical pixels, relative to the prototype origin.

    `left`/`right` extend along world +x and `bottom`/`top` along world +z,
    so with image y growing downward the anchor — the image pixel the
    prototype origin lands on — is (-left, top). Whole-pixel edges keep that
    anchor exact.
    """

    left: int
    right: int
    bottom: int
    top: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.top - self.bottom

    @property
    def size(self) -> PixelPair:
        return (self.width, self.height)

    @property
    def anchor(self) -> PixelPair:
        return (-self.left, self.top)

    def center_offset(self, *, pixels_per_unit: float) -> Tuple[float, float]:
        """World x/z offset from the prototype origin to the canvas center."""
        return (
            (self.left + self.right) / 2 / pixels_per_unit,
            (self.bottom + self.top) / 2 / pixels_per_unit,
        )

    def ortho_width(self, *, pixels_per_unit: float) -> float:
        return self.width / pixels_per_unit


def sprite_framing(bounds: Bounds, *, pixels_per_unit: float, padding_pixels: int) -> SpriteFraming:
    """Frame mesh bounds with padding, rounded out to whole logical pixels.

    The padding leaves room so edge antialiasing never clips at the canvas
    border.
    """
    (min_x, _, min_z), (max_x, _, max_z) = bounds
    return SpriteFraming(
        left=math.floor(min_x * pixels_per_unit) - padding_pixels,
        right=math.ceil(max_x * pixels_per_unit) + padding_pixels,
        bottom=math.floor(min_z * pixels_per_unit) - padding_pixels,
        top=math.ceil(max_z * pixels_per_unit) + padding_pixels,
    )


def strip_framing(
    bounds: Bounds,
    *,
    pixels_per_unit: float,
    width_pixels: float,
    padding_pixels: int,
) -> SpriteFraming:
    """Frame a full-board-width horizontal strip whose origin sits on the board's vertical center line.

    The fixed width lets the runtime blit the strip at x = 0 and stretch it
    to the screen width, so only the vertical extent comes from the mesh.

    Raises:
        ValueError: when the board width does not split into two whole pixel halves.
    """
    (_, _, min_z), (_, _, max_z) = bounds
    half_width = width_pixels / 2
    if not half_width.is_integer():
        raise ValueError(f"board width {width_pixels} does not split into whole pixel halves")

    return SpriteFraming(
        left=-int(half_width),
        right=int(half_width),
        bottom=math.floor(min_z * pixels_per_unit) - padding_pixels,
        top=math.ceil(max_z * pixels_per_unit) + padding_pixels,
    )


def shadow_framing(
    bounds: Bounds,
    *,
    pixels_per_unit: float,
    sun_direction: Vec3,
    catcher_y: float,
    margin_pixels: int,
) -> SpriteFraming:
    """Frame the shadow the mesh casts onto the catcher plane.

    Every mesh point travels along the sun direction until it hits the
    catcher, so the shadow region is the silhouette displaced by the offsets
    at the mesh's nearest and farthest depth; the margin absorbs the penumbra
    from the sun's angular size.

    Raises:
        ValueError: when the sun cannot project the mesh onto the catcher.
    """
    (min_x, min_y, min_z), (max_x, max_y, max_z) = bounds
    direction_x, direction_y, direction_z = sun_direction
    if direction_y <= 0.0:
        raise ValueError("the sun does not shine toward the catcher plane")

    if max_y >= catcher_y:
        raise ValueError("the mesh reaches behind the catcher plane")

    travels = tuple((catcher_y - depth) / direction_y for depth in (min_y, max_y))
    offsets_x = tuple(travel * direction_x for travel in travels)
    offsets_z = tuple(travel * direction_z for travel in travels)
    return SpriteFraming(
        left=math.floor((min_x + min(offsets_x)) * pixels_per_unit) - margin_pixels,
        right=math.ceil((max_x + max(offsets_x)) * pixels_per_unit) + margin_pixels,
        bottom=math.floor((min_z + min(offsets_z)) * pixels_per_unit) - margin_pixels,
        top=math.ceil((max_z + max(offsets_z)) * pixels_per_unit) + margin_pixels,
    )
