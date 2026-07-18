from pathlib import Path
from typing import Final

import bpy
import numpy as np

from locksmith.types import RGBAImage

_CHANNELS: Final[int] = 4
_BYTE_SCALE: Final[float] = 255.0


def read_rgba_pixels(path: Path) -> RGBAImage:
    """Decode an image file into an 8-bit RGBA array in top-down row order.

    `Image.pixels` exposes the raw stored values, so an 8-bit PNG round-trips
    exactly through the byte scale; Blender keeps rows bottom-up, hence the
    flip. The datablock is removed again — loading is purely a decode step.

    Raises:
        ValueError: when the image does not decode to four 8-bit channels.
    """
    image = bpy.data.images.load(str(path))
    try:
        width, height = image.size[0], image.size[1]
        if image.channels != _CHANNELS:
            raise ValueError(f"{path} decoded to {image.channels} channels, expected {_CHANNELS}")
        buffer = np.empty(width * height * _CHANNELS, dtype=np.float32)
        # The stub omits prop-array batch access and pylint misreads its runtime signature.
        # pylint: disable-next=too-many-function-args
        image.pixels.foreach_get(buffer)
    finally:
        bpy.data.images.remove(image)
    rows = np.rint(buffer.reshape((height, width, _CHANNELS)) * _BYTE_SCALE).astype(np.uint8)
    return np.ascontiguousarray(np.flipud(rows))
