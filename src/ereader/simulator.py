from __future__ import annotations

import time
from dataclasses import dataclass

import pygame
from PIL import Image

from .eink_effects import (
    DitherMode,
    DisplayMode,
    EinkEffectConfig,
    apply_eink_effects,
    flash_frame,
)


@dataclass
class SimulatorConfig:
    scale: float = 0.75
    effects: EinkEffectConfig | None = None


class EinkSimulator:
    def __init__(self, size: tuple[int, int], config: SimulatorConfig) -> None:
        self.size = size
        self.config = config
        self.effects = config.effects or EinkEffectConfig()
        self.previous: Image.Image | None = None
        self._flash_next = self.effects.full_refresh_flash

        pygame.init()
        window_size = (int(size[0] * config.scale), int(size[1] * config.scale))
        self.screen = pygame.display.set_mode(window_size)
        pygame.display.set_caption("EReader E-Ink Simulator")
        self.clock = pygame.time.Clock()

    def show(self, image: Image.Image, *, full_refresh: bool = False) -> None:
        full = full_refresh or self._flash_next
        if full and self.effects.full_refresh_flash:
            self._blit(flash_frame(self.size, invert=True))
            time.sleep(0.08)
            self._blit(flash_frame(self.size, invert=False))
            time.sleep(0.05)

        effected = apply_eink_effects(image, self.previous if not full else None, self.effects)
        self._blit(effected)
        self.previous = effected
        self._flash_next = False

    def handle_effect_key(self, key: int) -> bool:
        if key == pygame.K_1:
            self.effects.display_mode = DisplayMode.ONE_BIT
        elif key == pygame.K_2:
            self.effects.display_mode = DisplayMode.TWO_BIT
        elif key == pygame.K_4:
            self.effects.display_mode = DisplayMode.FOUR_BIT
        elif key == pygame.K_g:
            self.effects.ghosting = 0.0 if self.effects.ghosting > 0 else 0.16
        elif key == pygame.K_f:
            self.effects.full_refresh_flash = not self.effects.full_refresh_flash
        elif key == pygame.K_d:
            self.effects.dither_mode = _next_dither(self.effects.dither_mode)
        else:
            return False

        self._flash_next = True
        return True

    def tick(self) -> None:
        self.clock.tick(30)

    def close(self) -> None:
        pygame.quit()

    def _blit(self, image: Image.Image) -> None:
        rgb = image.convert("RGB")
        surface = pygame.image.fromstring(rgb.tobytes(), rgb.size, "RGB")
        if self.config.scale != 1:
            surface = pygame.transform.smoothscale(surface, self.screen.get_size())
        self.screen.blit(surface, (0, 0))
        pygame.display.flip()


def _next_dither(mode: DitherMode) -> DitherMode:
    order = [DitherMode.ORDERED, DitherMode.FLOYD, DitherMode.NONE]
    return order[(order.index(mode) + 1) % len(order)]

