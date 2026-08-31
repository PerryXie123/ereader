from __future__ import annotations

import argparse
from pathlib import Path

from .drivers.null import NullDisplayDriver
from .eink_effects import DitherMode, DisplayMode, EinkEffectConfig
from .framebuffer import DisplaySize, VirtualFramebuffer
from .ui import ReaderUI


def main() -> None:
    args = _parse_args()
    size = DisplaySize(width=args.width, height=args.height)
    framebuffer = VirtualFramebuffer(size)
    ui = ReaderUI(size)

    if args.target == "simulator":
        _run_simulator(args, framebuffer, ui)
    elif args.target == "null-hardware":
        _run_null_hardware(args, framebuffer, ui)
    else:
        raise ValueError(f"Unknown target: {args.target}")


def _run_simulator(args: argparse.Namespace, framebuffer: VirtualFramebuffer, ui: ReaderUI) -> None:
    import pygame

    from .simulator import EinkSimulator, SimulatorConfig

    effects = EinkEffectConfig(
        display_mode=DisplayMode(args.display_mode),
        dither_mode=DitherMode(args.dither),
        ghosting=args.ghosting,
        full_refresh_flash=args.full_refresh_flash,
    )
    simulator = EinkSimulator(
        (framebuffer.size.width, framebuffer.size.height),
        SimulatorConfig(scale=args.scale, effects=effects),
    )

    try:
        _render_to(framebuffer, ui, simulator.show, full_refresh=True)
        running = True
        while running:
            changed = False
            full_refresh = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    changed, full_refresh, running = _handle_key(event.key, ui, simulator)

            if changed:
                _render_to(framebuffer, ui, simulator.show, full_refresh=full_refresh)
            simulator.tick()
    finally:
        simulator.close()


def _run_null_hardware(args: argparse.Namespace, framebuffer: VirtualFramebuffer, ui: ReaderUI) -> None:
    driver = NullDisplayDriver(Path(args.output))
    _render_to(framebuffer, ui, driver.show, full_refresh=True)
    driver.close()


def _render_to(framebuffer: VirtualFramebuffer, ui: ReaderUI, show, *, full_refresh: bool) -> None:
    framebuffer.replace(ui.render())
    show(framebuffer.image, full_refresh=full_refresh)


def _handle_key(key: int, ui: ReaderUI, simulator) -> tuple[bool, bool, bool]:
    import pygame

    if key in {pygame.K_ESCAPE, pygame.K_q}:
        return False, False, False

    if simulator.handle_effect_key(key):
        return True, True, True

    if key in {pygame.K_RIGHT, pygame.K_SPACE, pygame.K_PAGEDOWN}:
        ui.next_page()
    elif key in {pygame.K_LEFT, pygame.K_BACKSPACE, pygame.K_PAGEUP}:
        ui.previous_page()
    elif key == pygame.K_HOME:
        ui.home()
    elif key == pygame.K_RETURN:
        ui.open_selected()
    elif key == pygame.K_DOWN:
        ui.select_next()
    elif key == pygame.K_UP:
        ui.select_previous()
    else:
        return False, False, True

    return True, False, True


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kindle-style e-ink reader simulator")
    parser.add_argument("--target", choices=["simulator", "null-hardware"], default="simulator")
    parser.add_argument("--width", type=int, default=758)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--scale", type=float, default=0.75)
    parser.add_argument("--display-mode", choices=[mode.value for mode in DisplayMode], default=DisplayMode.FOUR_BIT.value)
    parser.add_argument("--dither", choices=[mode.value for mode in DitherMode], default=DitherMode.ORDERED.value)
    parser.add_argument("--ghosting", type=float, default=0.12)
    parser.add_argument("--full-refresh-flash", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--output", default="out/latest-frame.png")
    return parser.parse_args()
