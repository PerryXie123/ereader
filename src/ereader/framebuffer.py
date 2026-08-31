from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class DisplaySize:
    width: int = 758
    height: int = 1024


class VirtualFramebuffer:
    """A tiny framebuffer wrapper shared by simulated and hardware outputs."""

    def __init__(self, size: DisplaySize) -> None:
        self.size = size
        self._image = Image.new("L", (size.width, size.height), 255)

    @property
    def image(self) -> Image.Image:
        return self._image

    def replace(self, image: Image.Image) -> None:
        expected = (self.size.width, self.size.height)
        if image.size != expected:
            raise ValueError(f"Framebuffer image must be {expected}, got {image.size}")
        self._image = image.convert("L")

    def clear(self, value: int = 255) -> None:
        self._image = Image.new("L", (self.size.width, self.size.height), value)

