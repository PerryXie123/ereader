# EReader E-Ink Simulator

A Raspberry Pi-friendly Kindle-style reader prototype built around a shared
virtual framebuffer.

The app renders every screen into one monochrome-oriented framebuffer. That
same framebuffer can be sent to:

- a desktop simulator window with e-ink effects
- a hardware display driver once you add a real e-ink panel

```text
Reader UI
   |
   v
Virtual framebuffer
   |
   +--> Desktop e-ink simulator
   |
   +--> Real e-ink display driver
```

## Features

- Fixed-size Kindle-like display target, default `758 x 1024`
- Library and reading screens
- Page-based navigation
- Grayscale, 1-bit, 2-bit, and 4-bit display modes
- Ordered and Floyd-Steinberg dithering
- Full-refresh flash simulation
- Partial-refresh ghosting simulation
- Hardware driver interface with a null driver and Waveshare-style stub

## Raspberry Pi Setup

On Raspberry Pi OS / Raspbian:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-pygame
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
python -m pip install -e .
```

The `--system-site-packages` flag lets the virtualenv see Raspberry Pi OS's
`python3-pygame` package.

## Run The Simulator

```bash
python -m ereader --target simulator
```

Useful options:

```bash
python -m ereader --width 758 --height 1024
python -m ereader --scale 0.75
python -m ereader --display-mode 1bit
python -m ereader --dither floyd
python -m ereader --ghosting 0.18
```

## Controls

- `Right`, `Space`, `PageDown`: next page
- `Left`, `Backspace`, `PageUp`: previous page
- `Home`: library
- `Enter`: open selected book
- `Up` / `Down`: select book in library
- `1`: 1-bit mode
- `2`: 2-bit mode
- `4`: 4-bit mode
- `G`: toggle ghosting
- `F`: toggle full-refresh flash
- `D`: cycle dithering
- `Esc` or `Q`: quit

## Hardware Driver Path

Run the same UI through the null hardware driver:

```bash
python -m ereader --target null-hardware
```

To connect a real e-ink panel, implement `DisplayDriver` in
`src/ereader/drivers/`. The UI will keep rendering to the same virtual
framebuffer, so the hardware driver only needs to translate a Pillow image into
the panel library's expected format.
