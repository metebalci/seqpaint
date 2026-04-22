from __future__ import annotations

import math
import warnings
from collections.abc import Iterator
from typing import Protocol


class Layout(Protocol):
    name: str

    def grid_for(
        self, length: int, aspect_ratio: tuple[int, int]
    ) -> tuple[int, int]: ...

    def coords(
        self, length: int, w: int, h: int
    ) -> Iterator[tuple[int, int]]: ...


class RasterLayout:
    name = "raster"

    def grid_for(self, length: int, aspect_ratio: tuple[int, int]) -> tuple[int, int]:
        aw, ah = aspect_ratio
        unit = max(math.floor(math.sqrt(length / (aw * ah))), 1)
        w = unit * aw
        h = unit * ah
        while length > (w * h):
            h += 1
        return w, h

    def coords(self, length: int, w: int, h: int) -> Iterator[tuple[int, int]]:
        i = 0
        for y in range(h):
            for x in range(w):
                if i == length:
                    return
                yield x, y
                i += 1


def _next_pow2_side(length: int) -> int:
    side = 1
    while side * side < length:
        side *= 2
    return side


class _SquarePow2Mixin:
    def grid_for(
        self, length: int, aspect_ratio: tuple[int, int]
    ) -> tuple[int, int]:
        if aspect_ratio != (1, 1):
            warnings.warn(
                f"{self.name!r} layout ignores aspect_ratio; forcing square grid",  # type: ignore[attr-defined]
                stacklevel=2,
            )
        n = _next_pow2_side(length)
        return n, n


class HilbertLayout(_SquarePow2Mixin):
    name = "hilbert"

    def coords(self, length: int, w: int, h: int) -> Iterator[tuple[int, int]]:
        n = w  # square, power of two
        for d in range(length):
            yield _hilbert_d2xy(n, d)


class ZOrderLayout(_SquarePow2Mixin):
    name = "zorder"

    def coords(self, length: int, w: int, h: int) -> Iterator[tuple[int, int]]:
        for d in range(length):
            yield _morton_d2xy(d)


def _hilbert_d2xy(n: int, d: int) -> tuple[int, int]:
    """Map distance d along the Hilbert curve to (x, y) on an n x n grid.

    n must be a power of two; 0 <= d < n*n.
    """
    x = 0
    y = 0
    t = d
    s = 1
    while s < n:
        rx = 1 & (t // 2)
        ry = 1 & (t ^ rx)
        if ry == 0:
            if rx == 1:
                x = s - 1 - x
                y = s - 1 - y
            x, y = y, x
        x += s * rx
        y += s * ry
        t //= 4
        s *= 2
    return x, y


def _morton_d2xy(d: int) -> tuple[int, int]:
    """Map distance d along the Z-order (Morton) curve to (x, y)."""
    x = 0
    y = 0
    for i in range(32):
        x |= ((d >> (2 * i)) & 1) << i
        y |= ((d >> (2 * i + 1)) & 1) << i
    return x, y


_LAYOUTS: dict[str, Layout] = {
    "raster": RasterLayout(),
    "hilbert": HilbertLayout(),
    "zorder": ZOrderLayout(),
}

LAYOUT_NAMES = tuple(_LAYOUTS.keys())


def get_layout(name: str) -> Layout:
    try:
        return _LAYOUTS[name]
    except KeyError as e:
        raise ValueError(
            f"unknown layout {name!r}; available: {list(_LAYOUTS)}"
        ) from e
