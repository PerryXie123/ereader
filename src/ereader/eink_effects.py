from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PIL import Image, ImageChops


class DisplayMode(str, Enum):
    ONE_BIT = "1bit"
    TWO_BIT = "2bit"
    FOUR_BIT = "4bit"
    GRAYSCALE = "gray"


class DitherMode(str, Enum):
    NONE = "none"
    ORDERED = "ordered"
    FLOYD = "floyd"


@dataclass
class EinkEffectConfig:
    display_mode: DisplayMode = DisplayMode.FOUR_BIT
    dither_mode: DitherMode = DitherMode.ORDERED
    ghosting: float = 0.12
    full_refresh_flash: bool = True


_BAYER_4X4 = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


def apply_eink_effects(
    image: Image.Image,
    previous: Image.Image | None,
    config: EinkEffectConfig,
) -> Image.Image:
    output = image.convert("L")

    if previous is not None and config.ghosting > 0:
        ghost = previous.convert("L")
        output = Image.blend(output, ghost, max(0.0, min(config.ghosting, 0.6)))

    if config.display_mode == DisplayMode.GRAYSCALE:
        return output

    if config.dither_mode == DitherMode.FLOYD:
        return _floyd_dither(output, config.display_mode)

    if config.dither_mode == DitherMode.ORDERED:
        return _ordered_dither(output, config.display_mode)

    return _quantize(output, config.display_mode)


def flash_frame(size: tuple[int, int], invert: bool) -> Image.Image:
    return Image.new("L", size, 0 if invert else 255)


def changed_bbox(previous: Image.Image | None, current: Image.Image) -> tuple[int, int, int, int] | None:
    if previous is None:
        return (0, 0, current.width, current.height)
    return ImageChops.difference(previous.convert("L"), current.convert("L")).getbbox()


def _levels_for_mode(mode: DisplayMode) -> int:
    if mode == DisplayMode.ONE_BIT:
        return 2
    if mode == DisplayMode.TWO_BIT:
        return 4
    if mode == DisplayMode.FOUR_BIT:
        return 16
    return 256


def _quantize(image: Image.Image, mode: DisplayMode) -> Image.Image:
    levels = _levels_for_mode(mode)
    if levels >= 256:
        return image

    step = 255 / (levels - 1)
    table = [round(round(value / step) * step) for value in range(256)]
    return image.point(table)


def _ordered_dither(image: Image.Image, mode: DisplayMode) -> Image.Image:
    levels = _levels_for_mode(mode)
    if levels >= 256:
        return image

    source = image.load()
    result = Image.new("L", image.size, 255)
    target = result.load()
    step = 255 / (levels - 1)

    for y in range(image.height):
        for x in range(image.width):
            threshold = (_BAYER_4X4[y % 4][x % 4] - 7.5) * (step / 16)
            value = max(0, min(255, source[x, y] + threshold))
            target[x, y] = round(round(value / step) * step)

    return result


def _floyd_dither(image: Image.Image, mode: DisplayMode) -> Image.Image:
    levels = _levels_for_mode(mode)
    if levels >= 256:
        return image

    width, height = image.size
    pixels = [float(v) for v in image.getdata()]
    step = 255 / (levels - 1)

    def index(px: int, py: int) -> int:
        return py * width + px

    for y in range(height):
        for x in range(width):
            old = pixels[index(x, y)]
            new = round(round(old / step) * step)
            pixels[index(x, y)] = new
            error = old - new

            if x + 1 < width:
                pixels[index(x + 1, y)] += error * 7 / 16
            if x > 0 and y + 1 < height:
                pixels[index(x - 1, y + 1)] += error * 3 / 16
            if y + 1 < height:
                pixels[index(x, y + 1)] += error * 5 / 16
            if x + 1 < width and y + 1 < height:
                pixels[index(x + 1, y + 1)] += error * 1 / 16

    clamped = [int(max(0, min(255, round(v)))) for v in pixels]
    result = Image.new("L", image.size)
    result.putdata(clamped)
    return result

