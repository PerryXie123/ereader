from __future__ import annotations

from abc import ABC, abstractmethod

from PIL import Image


class DisplayDriver(ABC):
    @abstractmethod
    def show(self, image: Image.Image, *, full_refresh: bool = False) -> None:
        """Display a grayscale framebuffer image."""

    def close(self) -> None:
        pass

