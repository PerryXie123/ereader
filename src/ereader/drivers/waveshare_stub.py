from __future__ import annotations

from PIL import Image

from .base import DisplayDriver


class WaveshareDisplayDriver(DisplayDriver):
    """Template for wiring the framebuffer to a Waveshare e-paper module."""

    def __init__(self) -> None:
        raise RuntimeError(
            "Install the Waveshare e-Paper library for your exact panel and "
            "replace this stub with that module's init/display calls."
        )

    def show(self, image: Image.Image, *, full_refresh: bool = False) -> None:
        panel_image = image.convert("1")
        _ = panel_image, full_refresh
        raise NotImplementedError("Send panel_image to the Waveshare display here.")

