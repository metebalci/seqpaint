from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from .layouts import get_layout

if TYPE_CHECKING:
    from .canvas import Canvas
    from .palette import Palette

RGBA = tuple[int, int, int, int]

UNKNOWN_KEY = "n"


def _as_palette(palette):
    from .palette import Palette as _P

    if isinstance(palette, _P):
        return palette
    colors = dict(palette)
    fallback = colors.get(UNKNOWN_KEY, (0xFF, 0xFF, 0xFF, 0xFF))
    return _P(colors=colors, fallback=fallback)


def _make_canvas(
    width: int, height: int, bg_color: RGBA, canvas: Canvas | None,
) -> Canvas:
    if canvas is not None:
        return canvas
    from .canvas import PngCanvas
    return PngCanvas(width, height, bg_color)


def paint(
    sequence: str,
    *,
    palette: Palette | Mapping[str, RGBA],
    pixel_size: int = 1,
    aspect_ratio: tuple[int, int] = (1, 1),
    bg_color: RGBA = (0, 0, 0, 255),
    layout: str = "raster",
    canvas: Canvas | None = None,
) -> Canvas:
    """Render a sequence into a Canvas using the chosen layout."""
    if pixel_size < 1:
        raise ValueError("pixel_size must be >= 1")
    aw, ah = aspect_ratio
    if aw < 1 or ah < 1:
        raise ValueError("aspect_ratio components must be >= 1")
    if not sequence:
        raise ValueError("sequence is empty")

    pal = _as_palette(palette)
    lay = get_layout(layout)
    w, h = lay.grid_for(len(sequence), aspect_ratio)
    c = _make_canvas(w * pixel_size, h * pixel_size, bg_color, canvas)

    for i, (x, y) in enumerate(lay.coords(len(sequence), w, h)):
        if i == len(sequence):
            break
        c.fill_rect(
            x * pixel_size, y * pixel_size, pixel_size, pixel_size,
            pal.get(sequence[i]),
        )
    return c


def paint_colors(
    colors: list[RGBA],
    *,
    pixel_size: int = 1,
    aspect_ratio: tuple[int, int] = (1, 1),
    bg_color: RGBA = (0, 0, 0, 255),
    layout: str = "raster",
    canvas: Canvas | None = None,
) -> Canvas:
    """Render a sequence of precomputed per-position RGBA colors."""
    if not colors:
        raise ValueError("colors is empty")
    if pixel_size < 1:
        raise ValueError("pixel_size must be >= 1")
    aw, ah = aspect_ratio
    if aw < 1 or ah < 1:
        raise ValueError("aspect_ratio components must be >= 1")

    lay = get_layout(layout)
    w, h = lay.grid_for(len(colors), aspect_ratio)
    c = _make_canvas(w * pixel_size, h * pixel_size, bg_color, canvas)
    for i, (x, y) in enumerate(lay.coords(len(colors), w, h)):
        if i == len(colors):
            break
        c.fill_rect(
            x * pixel_size, y * pixel_size, pixel_size, pixel_size, colors[i],
        )
    return c


def paint_values(
    values: list[float],
    *,
    pixel_size: int = 1,
    aspect_ratio: tuple[int, int] = (1, 1),
    bg_color: RGBA = (0, 0, 0, 255),
    layout: str = "raster",
    canvas: Canvas | None = None,
) -> Canvas:
    """Render a sequence of values in [0, 1] as a grayscale heatmap."""
    if not values:
        raise ValueError("values is empty")
    if pixel_size < 1:
        raise ValueError("pixel_size must be >= 1")
    aw, ah = aspect_ratio
    if aw < 1 or ah < 1:
        raise ValueError("aspect_ratio components must be >= 1")

    lay = get_layout(layout)
    w, h = lay.grid_for(len(values), aspect_ratio)
    c = _make_canvas(w * pixel_size, h * pixel_size, bg_color, canvas)
    for i, (x, y) in enumerate(lay.coords(len(values), w, h)):
        if i == len(values):
            break
        v = max(0.0, min(1.0, values[i]))
        g = round(v * 255)
        c.fill_rect(
            x * pixel_size, y * pixel_size, pixel_size, pixel_size,
            (g, g, g, 0xFF),
        )
    return c
