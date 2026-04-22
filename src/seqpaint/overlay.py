from __future__ import annotations

from collections.abc import Iterable, Mapping

from .canvas import Canvas
from .core import RGBA
from .gff import Feature
from .layouts import get_layout

DEFAULT_FEATURE_COLORS: dict[str, RGBA] = {
    "gene": (0xFF, 0xE0, 0x10, 0xFF),
    "cds": (0x00, 0xF0, 0xF0, 0xFF),
    "mrna": (0xA0, 0xA0, 0xFF, 0xFF),
    "exon": (0xFF, 0xFF, 0xFF, 0xFF),
    "five_prime_utr": (0xFF, 0x40, 0xFF, 0xFF),
    "three_prime_utr": (0xFF, 0x80, 0x40, 0xFF),
    "trna": (0x80, 0xFF, 0x80, 0xFF),
    "rrna": (0x40, 0xFF, 0xC0, 0xFF),
}


def overlay_annotations(
    canvas: Canvas,
    features: Iterable[Feature],
    *,
    sequence_length: int,
    pixel_size: int,
    aspect_ratio: tuple[int, int],
    layout: str,
    feature_colors: Mapping[str, RGBA] = DEFAULT_FEATURE_COLORS,
    include_types: set[str] | None = None,
) -> Canvas:
    """Draw feature outlines on `canvas` for each GFF feature.

    Only the raster layout is supported.
    """
    if layout != "raster":
        raise ValueError(
            "annotation overlay currently only supports --layout raster"
        )
    lay = get_layout(layout)
    w, _ = lay.grid_for(sequence_length, aspect_ratio)

    for feat in features:
        typ = feat.type.lower()
        if include_types is not None and typ not in include_types:
            continue
        color = feature_colors.get(typ)
        if color is None:
            continue
        s = max(0, feat.start - 1)
        e = min(sequence_length, feat.end)
        if s >= e:
            continue
        y_start = s // w
        y_end = (e - 1) // w
        for y in range(y_start, y_end + 1):
            row_s = max(s, y * w)
            row_e = min(e, (y + 1) * w)
            x0 = (row_s - y * w) * pixel_size
            x1 = (row_e - y * w) * pixel_size
            y0 = y * pixel_size
            canvas.stroke_rect(x0, y0, x1 - x0, pixel_size, color)
    return canvas
