from itertools import pairwise

import pytest

from seqpaint import get_layout


def _collect(name: str, length: int, w: int, h: int):
    return list(get_layout(name).coords(length, w, h))


def test_raster_grid_shape():
    lay = get_layout("raster")
    assert lay.grid_for(24, (3, 2)) == (6, 4)


def test_raster_coords_are_unique_and_in_bounds():
    coords = _collect("raster", 24, 6, 4)
    assert len(coords) == 24
    assert len(set(coords)) == 24
    for x, y in coords:
        assert 0 <= x < 6 and 0 <= y < 4


def test_hilbert_grid_is_square_power_of_two():
    lay = get_layout("hilbert")
    w, h = lay.grid_for(100, (1, 1))
    assert w == h == 16  # smallest 2^k with k*k >= 100


def test_hilbert_coords_are_unique():
    coords = _collect("hilbert", 200, 16, 16)
    assert len(coords) == 200
    assert len(set(coords)) == 200
    for x, y in coords:
        assert 0 <= x < 16 and 0 <= y < 16


def test_hilbert_preserves_locality():
    # Adjacent sequence indices should map to adjacent (Manhattan=1) pixels.
    coords = _collect("hilbert", 256, 16, 16)
    for a, b in pairwise(coords):
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def test_zorder_coords_are_unique_and_in_bounds():
    coords = _collect("zorder", 64, 8, 8)
    assert len(coords) == 64
    assert len(set(coords)) == 64
    for x, y in coords:
        assert 0 <= x < 8 and 0 <= y < 8


def test_unknown_layout_raises():
    with pytest.raises(ValueError):
        get_layout("spiral")
