from __future__ import annotations

import argparse
from pathlib import Path

from ..canvas import canvas_for
from ..compare import diff_image, dotplot_image, needleman_wunsch, stacked_image
from ..io import read_fasta
from ..palette import Palette
from .detect import detect_alphabet_from_sequence


def run_dotplot(args: argparse.Namespace, path: Path, path2: Path) -> int:
    a = _first_sequence(path)
    b = _first_sequence(path2)
    if a is None or b is None:
        return 1
    print(f"dotplot: seq_a={len(a)}, seq_b={len(b)}, k={args.word_size}")
    out = Path(args.output)
    try:
        na = max(0, len(a) - args.word_size + 1)
        nb = max(0, len(b) - args.word_size + 1)
        step_a = max(1, (na + args.max_cells - 1) // args.max_cells)
        step_b = max(1, (nb + args.max_cells - 1) // args.max_cells)
        cells_a = (na + step_a - 1) // step_a
        cells_b = (nb + step_b - 1) // step_b
        canvas = canvas_for(
            out, cells_a * args.pixel_size, cells_b * args.pixel_size,
            tuple(args.bg_color),  # type: ignore[arg-type]
        )
        dotplot_image(
            a, b,
            word_size=args.word_size,
            max_cells=args.max_cells,
            bg_color=tuple(args.bg_color),  # type: ignore[arg-type]
            pixel_size=args.pixel_size,
            canvas=canvas,
        )
    except ValueError as e:
        print(f"dotplot: {e}")
        return 2
    canvas.save(out)
    return 0


def run_diff(args: argparse.Namespace, path: Path, path2: Path) -> int:
    a = _first_sequence(path)
    b = _first_sequence(path2)
    if a is None or b is None:
        return 1
    print(f"diff: seq_a={len(a)}, seq_b={len(b)}")
    out = Path(args.output)
    try:
        aa, _bb = needleman_wunsch(a, b)
        canvas = canvas_for(
            out, len(aa) * args.pixel_size, 2 * args.pixel_size,
            tuple(args.bg_color),  # type: ignore[arg-type]
        )
        diff_image(
            a, b,
            length_cap=args.length_cap,
            bg_color=tuple(args.bg_color),  # type: ignore[arg-type]
            pixel_size=args.pixel_size,
            canvas=canvas,
        )
    except ValueError as e:
        print(f"diff: {e}")
        return 2
    canvas.save(out)
    return 0


def run_stacked(args: argparse.Namespace, path: Path) -> int:
    records = read_fasta(path)
    if not records:
        print(f"no sequences in {path}")
        return 1
    alphabet = detect_alphabet_from_sequence(records[0].sequence)
    palette = Palette.named(args.palette, alphabet=alphabet)
    normalized = [
        (r.description, _normalize(r.sequence, alphabet)) for r in records
    ]
    max_len = max(len(s) for _, s in normalized)
    print(
        f"stacked: {len(normalized)} records (alphabet={alphabet}), widest={max_len}"
    )
    out = Path(args.output)
    canvas = canvas_for(
        out,
        max_len * args.pixel_size,
        len(normalized) * args.pixel_size,
        tuple(args.bg_color),  # type: ignore[arg-type]
    )
    stacked_image(
        normalized,
        palette=palette,
        pixel_size=args.pixel_size,
        bg_color=tuple(args.bg_color),  # type: ignore[arg-type]
        canvas=canvas,
    )
    canvas.save(out)
    return 0


def _first_sequence(path: Path) -> str | None:
    records = read_fasta(path)
    if not records:
        print(f"no sequences in {path}")
        return None
    return records[0].sequence.lower()


def _normalize(seq: str, alphabet: str) -> str:
    return seq.lower().replace("u", "t") if alphabet == "nucleic" else seq.lower()
