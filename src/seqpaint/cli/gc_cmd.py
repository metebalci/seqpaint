from __future__ import annotations

import argparse
from pathlib import Path

from ..canvas import canvas_for
from ..core import paint_values
from ..io import read_fasta
from ..layouts import get_layout


def run(args: argparse.Namespace, path: Path) -> int:
    if args.window < 1:
        print("--window must be >= 1")
        return 2
    step = args.step if args.step is not None else args.window
    if step < 1:
        print("--step must be >= 1")
        return 2

    records = read_fasta(path)
    if not records:
        print(f"no sequences in {path}")
        return 1
    rec = records[0]
    seq = rec.sequence.lower().replace("u", "t")
    print(f"seqdesc: {rec.description}")
    print(f"seqlen: {len(seq)}")

    values = _gc_windows(seq, args.window, step)
    if not values:
        print(f"sequence shorter than window ({len(seq)} < {args.window})")
        return 1
    print(f"windows: {len(values)} (window={args.window}, step={step})")

    out = Path(args.output)
    lay = get_layout(args.layout)
    cells_w, cells_h = lay.grid_for(len(values), tuple(args.aspect_ratio))
    canvas = canvas_for(
        out,
        cells_w * args.pixel_size,
        cells_h * args.pixel_size,
        tuple(args.bg_color),  # type: ignore[arg-type]
    )
    paint_values(
        values,
        pixel_size=args.pixel_size,
        aspect_ratio=tuple(args.aspect_ratio),  # type: ignore[arg-type]
        bg_color=tuple(args.bg_color),  # type: ignore[arg-type]
        layout=args.layout,
        canvas=canvas,
    )
    canvas.save(out)
    return 0


def _gc_windows(seq: str, window: int, step: int) -> list[float]:
    out: list[float] = []
    for start in range(0, len(seq) - window + 1, step):
        chunk = seq[start : start + window]
        gc = sum(1 for c in chunk if c in "gc")
        valid = sum(1 for c in chunk if c in "acgt")
        out.append(gc / valid if valid else 0.0)
    return out
