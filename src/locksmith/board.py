from dataclasses import dataclass

from locksmith.schema.models.board import BoardConfig


@dataclass(frozen=True)
class BoardGeometry:
    """Logical pixel layout mapped into Blender world units.

    The board plane is centered on the world origin with x rightward and z
    upward, while logical pixels anchor at the top-left with y downward, so
    the mapping recenters horizontally and flips the vertical axis.
    """

    config: BoardConfig

    @property
    def width(self) -> float:
        return self.units(self.config.width_pixels)

    @property
    def height(self) -> float:
        return self.units(self.config.height_pixels)

    @property
    def column_width(self) -> float:
        return self.units(self.config.column_width_pixels)

    def units(self, pixels: float) -> float:
        return pixels / self.config.pixels_per_unit

    def x_at(self, pixel_x: float) -> float:
        return self.units(pixel_x - self.config.width_pixels / 2)

    def column_center_x(self, position: int) -> float:
        center_pixels = (
            self.config.column_offset_pixels
            + position * self.config.column_pitch_pixels
            + self.config.column_width_pixels / 2
        )
        return self.x_at(center_pixels)

    def tip_z(self, *, upper: bool, height: float) -> float:
        """Height of a pin's free tip; upper pins hang from the top edge, lower pins stand on the bottom."""
        if upper:
            return self.height / 2 - height

        return -self.height / 2 + height
