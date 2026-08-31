from __future__ import annotations

from pathlib import Path

from PIL import Image

from .base import DisplayDriver


class NullDisplayDriver(DisplayDriver):
    """Hardware-driver placeholder that writes the latest frame to disk."""

    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def show(self, image: Image.Image, *, full_refresh: bool = False) -> None:
        image.convert("L").save(self.output_path)
        refresh = "full" if full_refresh else "partial"
        print(f"Wrote {refresh} refresh frame to {self.output_path}")

