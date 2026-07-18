import struct
import zlib
from pathlib import Path
from typing import Final

from locksmith.types import PixelPair, RGBAImage

# The preview compositor writes PNGs directly so no color management can
# touch the composited bytes; reading rendered output goes through Blender
# (locksmith.blender.images), which already ships every PNG filter decoder.

_SIGNATURE: Final[bytes] = b"\x89PNG\r\n\x1a\n"
_HEADER_TAG: Final[bytes] = b"IHDR"
_DATA_TAG: Final[bytes] = b"IDAT"
_END_TAG: Final[bytes] = b"IEND"
_HEADER_FORMAT: Final[str] = ">II5B"
_BIT_DEPTH: Final[int] = 8
_RGBA_COLOR_TYPE: Final[int] = 6
_NO_FILTER: Final[bytes] = b"\x00"
_CHANNELS: Final[int] = 4


def write_rgba(path: Path, image: RGBAImage) -> None:
    """Write an 8-bit RGBA array as an unfiltered PNG.

    Raises:
        ValueError: when the array is not a height x width x 4 uint8 image.
    """
    if image.ndim != 3 or image.shape[2] != _CHANNELS or image.dtype.name != "uint8":
        raise ValueError(f"expected a height x width x {_CHANNELS} uint8 image, got {image.dtype} {image.shape}")
    height, width = image.shape[0], image.shape[1]
    header = struct.pack(_HEADER_FORMAT, width, height, _BIT_DEPTH, _RGBA_COLOR_TYPE, 0, 0, 0)
    scanlines = b"".join(_NO_FILTER + row.tobytes() for row in image)
    path.write_bytes(
        _SIGNATURE + _chunk(_HEADER_TAG, header) + _chunk(_DATA_TAG, zlib.compress(scanlines)) + _chunk(_END_TAG, b"")
    )


def png_size(path: Path) -> PixelPair:
    """Read image dimensions from a PNG header.

    Raises:
        ValueError: when the file is not a PNG.
    """
    with path.open("rb") as stream:
        prefix = stream.read(len(_SIGNATURE) + 8 + struct.calcsize(_HEADER_FORMAT))
    if not prefix.startswith(_SIGNATURE) or prefix[len(_SIGNATURE) + 4 : len(_SIGNATURE) + 8] != _HEADER_TAG:
        raise ValueError(f"{path} is not a PNG file")
    width, height = struct.unpack_from(">II", prefix, len(_SIGNATURE) + 8)
    return width, height


def require_png_size(path: Path, expected: PixelPair) -> None:
    """Assert a rendered file's dimensions before it enters the manifest.

    Raises:
        ValueError: when the file is missing, not a PNG, or the wrong size.
    """
    actual = png_size(path)
    if actual != expected:
        raise ValueError(f"{path} is {actual[0]}x{actual[1]}, expected {expected[0]}x{expected[1]}")


def _chunk(tag: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload))
