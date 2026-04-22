from __future__ import annotations

import argparse
from pathlib import Path

from ..canvas import HtmlCanvas, canvas_for
from ..core import paint, paint_colors
from ..gff import Feature, read_gff
from ..io import FastaRecord, read_fasta
from ..kmer import kmer_colors
from ..layouts import get_layout
from ..overlay import overlay_annotations
from ..palette import Palette
from .detect import Alphabet


def run(args: argparse.Namespace, path: Path, alphabet: Alphabet) -> int:
    records = read_fasta(path)
    if not records:
        print(f"no sequences in {path}")
        return 1

    palette = _build_palette(args, alphabet)
    bg = tuple(args.bg_color)
    ar = tuple(args.aspect_ratio)

    kmer: int | None = args.kmer
    if kmer is not None and kmer < 1:
        print("--kmer must be >= 1")
        return 2

    features: list[Feature] | None = None
    include_types: set[str] | None = None
    if args.annotations is not None:
        if args.layout != "raster":
            print("--annotations requires --layout raster")
            return 2
        features = read_gff(args.annotations)
        if args.annotation_types:
            include_types = {t.lower() for t in args.annotation_types}
        print(f"annotations: {len(features)} features from {args.annotations}")

    mode = args.multi_mode if alphabet == "nucleic" else "first"

    if mode == "first":
        rec = records[0]
        _paint_record(
            rec, _resolve_output(args.output, rec),
            palette, bg, ar, args.pixel_size, args.layout, alphabet,
            kmer, features, include_types,
        )
    elif mode == "combined":
        combined = _normalize(
            "".join(r.sequence for r in records), alphabet
        )
        out = Path(args.output) if args.output else Path(records[0].description + ".png")
        print(f"seqdesc: combined ({len(records)} records)")
        print(f"seqlen: {len(combined)}")
        _save(
            combined, f"combined ({len(records)} records)",
            out, palette, bg, ar, args.pixel_size, args.layout,
            kmer, features, include_types,
        )
    else:
        for i, rec in enumerate(records, start=1):
            if args.output is None:
                out = Path(rec.description + ".png")
            else:
                stem = Path(args.output)
                out = stem.with_name(f"{stem.stem}{i}{stem.suffix or '.png'}")
            _paint_record(
                rec, out, palette, bg, ar, args.pixel_size, args.layout, alphabet,
                kmer, features, include_types,
            )
    return 0


def _build_palette(args: argparse.Namespace, alphabet: Alphabet) -> Palette:
    palette = Palette.named(args.palette, alphabet=alphabet)
    if alphabet == "nucleic":
        overrides = {}
        for base in ("a", "g", "c", "t", "n"):
            val = getattr(args, f"color_{base}")
            if val is not None:
                overrides[base] = tuple(val)
        if overrides:
            palette = palette.with_overrides(overrides)  # type: ignore[arg-type]
    else:
        amino_overrides: dict[str, tuple[int, int, int, int]] = {}
        amino_overrides["-"] = tuple(args.bg_color)  # type: ignore[assignment]
        if args.b_is is not None:
            amino_overrides["b"] = palette.get(args.b_is)
        if args.j_is is not None:
            amino_overrides["j"] = palette.get(args.j_is)
        if args.z_is is not None:
            amino_overrides["z"] = palette.get(args.z_is)
        palette = palette.with_overrides(amino_overrides)
    return palette


def _paint_record(
    rec: FastaRecord, out: Path, palette: Palette,
    bg: tuple, ar: tuple, pixel_size: int, layout: str, alphabet: Alphabet,
    kmer: int | None,
    features: list[Feature] | None,
    include_types: set[str] | None,
) -> None:
    seq = _normalize(rec.sequence, alphabet)
    print(f"seqdesc: {rec.description}")
    print(f"seqlen: {len(seq)}")
    _save(
        seq, rec.description, out, palette, bg, ar, pixel_size, layout,
        kmer, features, include_types,
    )


def _save(
    seq: str, description: str, out: Path, palette: Palette,
    bg: tuple, ar: tuple, pixel_size: int, layout: str,
    kmer: int | None,
    features: list[Feature] | None,
    include_types: set[str] | None,
) -> None:
    lay = get_layout(layout)
    cells_w, cells_h = lay.grid_for(len(seq), ar)
    canvas = canvas_for(
        out, cells_w * pixel_size, cells_h * pixel_size, bg,  # type: ignore[arg-type]
    )
    if isinstance(canvas, HtmlCanvas):
        index_map = [-1] * (cells_w * cells_h)
        for i, (x, y) in enumerate(lay.coords(len(seq), cells_w, cells_h)):
            if i >= len(seq):
                break
            index_map[y * cells_w + x] = i
        canvas.attach_sequence(
            seq, description, pixel_size=pixel_size, index_map=index_map,
        )

    if kmer is not None:
        colors = kmer_colors(seq, kmer, invalid=bg)  # type: ignore[arg-type]
        paint_colors(
            colors, pixel_size=pixel_size,
            aspect_ratio=ar,  # type: ignore[arg-type]
            bg_color=bg,  # type: ignore[arg-type]
            layout=layout, canvas=canvas,
        )
    else:
        paint(
            seq, palette=palette, pixel_size=pixel_size,
            aspect_ratio=ar,  # type: ignore[arg-type]
            bg_color=bg,  # type: ignore[arg-type]
            layout=layout, canvas=canvas,
        )
    if features is not None:
        overlay_annotations(
            canvas, features,
            sequence_length=len(seq),
            pixel_size=pixel_size,
            aspect_ratio=ar,  # type: ignore[arg-type]
            layout=layout,
            include_types=include_types,
        )
    canvas.save(out)


def _normalize(seq: str, alphabet: Alphabet) -> str:
    return seq.lower().replace("u", "t") if alphabet == "nucleic" else seq.lower()


def _resolve_output(given: str | None, rec: FastaRecord) -> Path:
    return Path(given) if given is not None else Path(rec.description + ".png")
