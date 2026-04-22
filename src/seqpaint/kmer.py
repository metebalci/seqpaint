from __future__ import annotations

import colorsys
import hashlib

from .core import RGBA

_VALID = set("acgt")


def kmer_colors(
    sequence: str,
    k: int,
    *,
    invalid: RGBA = (0, 0, 0, 255),
    saturation: float = 0.7,
    value: float = 0.9,
) -> list[RGBA]:
    """Return one RGBA color per position based on the k-mer starting there.

    The k-mer at position i is sequence[i:i+k]; its blake2b hash determines
    hue on the HSV wheel (fixed saturation and value) so that distinct
    k-mers produce visually distinct colors. Positions whose k-mer contains
    a non-{a,c,g,t} character (e.g. N) get the invalid color. Positions
    within the final k-1 bases fall back to invalid because no full k-mer
    starts there.
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    n = len(sequence)
    out: list[RGBA] = []
    for i in range(n):
        if i + k > n:
            out.append(invalid)
            continue
        kmer = sequence[i : i + k]
        if not all(c in _VALID for c in kmer):
            out.append(invalid)
            continue
        out.append(_hash_to_rgba(kmer, saturation, value))
    return out


def _hash_to_rgba(kmer: str, s: float, v: float) -> RGBA:
    digest = hashlib.blake2b(kmer.encode("ascii"), digest_size=2).digest()
    hue = int.from_bytes(digest, "big") / 65535
    r, g, b = colorsys.hsv_to_rgb(hue, s, v)
    return (round(r * 255), round(g * 255), round(b * 255), 255)
