from __future__ import annotations

from typing import TYPE_CHECKING

from .core import RGBA

if TYPE_CHECKING:
    from .canvas import Canvas


def _make_canvas(w: int, h: int, bg: RGBA, canvas):
    if canvas is not None:
        return canvas
    from .canvas import PngCanvas
    return PngCanvas(w, h, bg)


def dotplot_image(
    seq_a: str,
    seq_b: str,
    *,
    word_size: int = 10,
    max_cells: int = 4000,
    hit_color: RGBA = (0x20, 0xE0, 0x20, 0xFF),
    bg_color: RGBA = (0, 0, 0, 255),
    pixel_size: int = 1,
    canvas: Canvas | None = None,
) -> Canvas:
    if word_size < 1:
        raise ValueError("word_size must be >= 1")
    if max_cells < 1:
        raise ValueError("max_cells must be >= 1")
    if pixel_size < 1:
        raise ValueError("pixel_size must be >= 1")

    a = seq_a.lower()
    b = seq_b.lower()
    na = max(0, len(a) - word_size + 1)
    nb = max(0, len(b) - word_size + 1)
    if na == 0 or nb == 0:
        raise ValueError("both sequences must be >= word_size")

    step_a = max(1, (na + max_cells - 1) // max_cells)
    step_b = max(1, (nb + max_cells - 1) // max_cells)
    cells_a = (na + step_a - 1) // step_a
    cells_b = (nb + step_b - 1) // step_b

    index: dict[str, list[int]] = {}
    for j in range(nb):
        kmer = b[j : j + word_size]
        index.setdefault(kmer, []).append(j)

    hits: set[tuple[int, int]] = set()
    for i in range(na):
        kmer = a[i : i + word_size]
        js = index.get(kmer)
        if not js:
            continue
        ci = i // step_a
        for j in js:
            hits.add((ci, j // step_b))

    w = cells_a * pixel_size
    h = cells_b * pixel_size
    c = _make_canvas(w, h, bg_color, canvas)
    for ci, cj in hits:
        c.fill_rect(ci * pixel_size, cj * pixel_size, pixel_size, pixel_size, hit_color)
    return c


def needleman_wunsch(
    a: str, b: str, *, match: int = 1, mismatch: int = -1, gap: int = -2,
) -> tuple[str, str]:
    n = len(a)
    m = len(b)
    score: list[list[int]] = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        score[i][0] = score[i - 1][0] + gap
    for j in range(1, m + 1):
        score[0][j] = score[0][j - 1] + gap
    for i in range(1, n + 1):
        ai = a[i - 1]
        row = score[i]
        prev = score[i - 1]
        for j in range(1, m + 1):
            s = match if ai == b[j - 1] else mismatch
            row[j] = max(prev[j - 1] + s, prev[j] + gap, row[j - 1] + gap)
    out_a: list[str] = []
    out_b: list[str] = []
    i, j = n, m
    while i > 0 and j > 0:
        s = match if a[i - 1] == b[j - 1] else mismatch
        if score[i][j] == score[i - 1][j - 1] + s:
            out_a.append(a[i - 1])
            out_b.append(b[j - 1])
            i -= 1
            j -= 1
        elif score[i][j] == score[i - 1][j] + gap:
            out_a.append(a[i - 1])
            out_b.append("-")
            i -= 1
        else:
            out_a.append("-")
            out_b.append(b[j - 1])
            j -= 1
    while i > 0:
        out_a.append(a[i - 1])
        out_b.append("-")
        i -= 1
    while j > 0:
        out_a.append("-")
        out_b.append(b[j - 1])
        j -= 1
    return "".join(reversed(out_a)), "".join(reversed(out_b))


def diff_image(
    seq_a: str, seq_b: str, *,
    length_cap: int = 5000,
    match_color: RGBA = (0x30, 0xC0, 0x30, 0xFF),
    mismatch_color: RGBA = (0xD0, 0x30, 0x30, 0xFF),
    gap_color: RGBA = (0x60, 0x60, 0x60, 0xFF),
    bg_color: RGBA = (0, 0, 0, 255),
    pixel_size: int = 1,
    canvas: Canvas | None = None,
) -> Canvas:
    if max(len(seq_a), len(seq_b)) > length_cap:
        raise ValueError(
            f"diff mode caps sequence length at {length_cap} "
            f"(got {len(seq_a)} and {len(seq_b)}); use --length-cap to override"
        )
    if pixel_size < 1:
        raise ValueError("pixel_size must be >= 1")

    aligned_a, aligned_b = needleman_wunsch(seq_a.lower(), seq_b.lower())
    n = len(aligned_a)
    w = n * pixel_size
    h = 2 * pixel_size
    c = _make_canvas(w, h, bg_color, canvas)
    for i, (ca, cb) in enumerate(zip(aligned_a, aligned_b, strict=True)):
        x0 = i * pixel_size
        color_a = _diff_cell_color(ca, cb, match_color, mismatch_color, gap_color)
        color_b = _diff_cell_color(cb, ca, match_color, mismatch_color, gap_color)
        c.fill_rect(x0, 0, pixel_size, pixel_size, color_a)
        c.fill_rect(x0, pixel_size, pixel_size, pixel_size, color_b)
    return c


def _diff_cell_color(
    c: str, other: str, match: RGBA, mismatch: RGBA, gap: RGBA,
) -> RGBA:
    if c == "-":
        return gap
    return match if c == other else mismatch


def stacked_image(
    sequences: list[tuple[str, str]], *,
    palette,  # Palette
    pixel_size: int = 1,
    bg_color: RGBA = (0, 0, 0, 255),
    canvas: Canvas | None = None,
) -> Canvas:
    if not sequences:
        raise ValueError("sequences is empty")
    if pixel_size < 1:
        raise ValueError("pixel_size must be >= 1")

    max_len = max(len(s) for _, s in sequences)
    w = max_len * pixel_size
    h = len(sequences) * pixel_size
    c = _make_canvas(w, h, bg_color, canvas)
    for row, (_, seq) in enumerate(sequences):
        y0 = row * pixel_size
        for col, ch in enumerate(seq):
            x0 = col * pixel_size
            c.fill_rect(x0, y0, pixel_size, pixel_size, palette.get(ch))
    return c
