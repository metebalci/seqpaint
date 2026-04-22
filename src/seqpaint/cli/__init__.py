from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ..fetch import fetch_accession
from ..layouts import LAYOUT_NAMES
from ..palette import PALETTE_NAMES
from . import compare_cmd, gc_cmd, paint_cmd
from .detect import Alphabet, detect_alphabet_from_accession


def _add_shared_args(
    p: argparse.ArgumentParser, *,
    default_output: bool,
    include_palette: bool = True,
) -> None:
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--input", metavar="PATH",
        help=(
            "input FASTA file (plain .fna/.faa or compressed .gz; "
            ".bgz/.bgzf requires the 'bgzf' extra)"
        ),
    )
    src.add_argument(
        "--accession", metavar="ID",
        help=(
            "fetch the sequence from NCBI by accession (e.g. NC_045512.2); "
            "cached at $XDG_CACHE_HOME/seqpaint (default ~/.cache/seqpaint)"
        ),
    )
    p.add_argument(
        "--output", metavar="PATH", required=not default_output,
        help=(
            "output PNG path"
            + (
                "; may be omitted to derive from the sequence description"
                if default_output else ""
            )
        ),
    )
    p.add_argument(
        "--pixel-size", type=int, default=1, metavar="N",
        help="size in screen pixels of a single cell (default: 1)",
    )
    p.add_argument(
        "--aspect-ratio", type=int, nargs=2, default=[1, 1], metavar=("W", "H"),
        help=(
            "image aspect ratio as two integers (default: 1 1). "
            "Ignored by hilbert/zorder layouts."
        ),
    )
    p.add_argument(
        "--bg-color", type=int, nargs=4, default=[0, 0, 0, 255],
        metavar=("R", "G", "B", "A"),
        help="background RGBA 0..255 (default: 0 0 0 255, opaque black)",
    )
    if include_palette:
        p.add_argument(
            "--palette", choices=PALETTE_NAMES, default="default",
            help=(
                "named color palette: default, nature, colorblind-safe, "
                "grayscale. Nucleic and amino alphabets have different "
                "palette definitions."
            ),
        )
    p.add_argument(
        "--layout", choices=LAYOUT_NAMES, default="raster",
        help=(
            "pixel layout: raster, hilbert (locality-preserving space-filling "
            "curve), zorder (Morton curve)"
        ),
    )


def _add_second_input(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--input2", metavar="PATH",
        help="second input FASTA (alternative to --accession2)",
    )
    p.add_argument(
        "--accession2", metavar="ID",
        help="second NCBI accession (alternative to --input2)",
    )


def _color_arg(p, base: str, label: str) -> None:
    p.add_argument(
        f"--color-{base}", type=int, nargs=4, metavar=("R", "G", "B", "A"),
        help=f"override RGBA for {label}",
    )


def _configure_fna(p: argparse.ArgumentParser) -> None:
    _add_shared_args(p, default_output=True)
    p.add_argument(
        "--multi-mode",
        choices=["first", "separate", "combined"], default="first",
        help=(
            "how to handle multi-record FASTA: 'first' renders only the "
            "first record (default), 'separate' writes one PNG per record, "
            "'combined' concatenates all records"
        ),
    )
    p.add_argument(
        "--kmer", type=int, default=None, metavar="K",
        help=(
            "color each pixel by a hash of its k-mer instead of the single "
            "base; reveals repeats and low-complexity regions"
        ),
    )
    p.add_argument(
        "--annotations", metavar="PATH",
        help=(
            "GFF3 file to overlay as feature outlines. Requires --layout raster."
        ),
    )
    p.add_argument(
        "--annotation-types", nargs="+", metavar="TYPE",
        help="restrict annotation overlay to these GFF feature types",
    )
    _color_arg(p, "a", "adenine")
    _color_arg(p, "g", "guanine")
    _color_arg(p, "c", "cytosine")
    _color_arg(p, "t", "thymine (and uracil)")
    _color_arg(p, "n", "unknown / other base")
    # Amino-only flags are not accepted here; set to None so paint_cmd's
    # reject-incompatible path sees consistent defaults.
    p.set_defaults(b_is=None, j_is=None, z_is=None)


def _configure_faa(p: argparse.ArgumentParser) -> None:
    _add_shared_args(p, default_output=True)
    p.add_argument(
        "--b-is", choices=["d", "n"],
        help="fold B (Asp/Asn) into D or N's color",
    )
    p.add_argument(
        "--j-is", choices=["l", "i"],
        help="fold J (Leu/Ile) into L or I's color",
    )
    p.add_argument(
        "--z-is", choices=["e", "q"],
        help="fold Z (Glu/Gln) into E or Q's color",
    )
    # Nucleic-only flags are not accepted here; set defaults so paint_cmd's
    # reject-incompatible path sees consistent state.
    p.set_defaults(
        multi_mode="first", kmer=None, annotations=None,
        annotation_types=None,
        color_a=None, color_g=None, color_c=None, color_t=None, color_n=None,
    )


def _configure_gc(p: argparse.ArgumentParser) -> None:
    _add_shared_args(p, default_output=False)
    p.add_argument(
        "--window", type=int, default=100, metavar="N",
        help="sliding window size in bases (default: 100)",
    )
    p.add_argument(
        "--step", type=int, default=None, metavar="N",
        help="window step in bases (default: same as --window, non-overlapping)",
    )


def _configure_dotplot(p: argparse.ArgumentParser) -> None:
    _add_shared_args(p, default_output=False, include_palette=False)
    _add_second_input(p)
    p.add_argument(
        "--word-size", type=int, default=10, metavar="K",
        help="k-mer word size for dotplot matches (default: 10)",
    )
    p.add_argument(
        "--max-cells", type=int, default=4000, metavar="N",
        help="downsample to at most N cells per axis (default: 4000)",
    )


def _configure_diff(p: argparse.ArgumentParser) -> None:
    _add_shared_args(p, default_output=False, include_palette=False)
    _add_second_input(p)
    p.add_argument(
        "--length-cap", type=int, default=5000, metavar="N",
        help="refuse diff for sequences longer than this (default: 5000)",
    )


def _configure_stacked(p: argparse.ArgumentParser) -> None:
    _add_shared_args(p, default_output=False)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="seqpaint",
        description=(
            "Visualize nucleic-acid and protein sequences as images. "
            "Each subcommand implements a different rendering mode."
        ),
        epilog=(
            "examples:\n"
            "  seqpaint fna     --input genome.fna --output g.png\n"
            "  seqpaint fna     --accession NC_045512.2 --output c.png --layout hilbert\n"
            "  seqpaint faa     --input protein.faa --output p.png --palette nature\n"
            "  seqpaint gc      --input genome.fna --output gc.png --window 100\n"
            "  seqpaint dotplot --input A.fna --input2 B.fna --output dp.png\n"
            "  seqpaint diff    --input A.fna --input2 B.fna --output diff.png\n"
            "  seqpaint stacked --input multi.fna --output s.png"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="command", required=True, metavar="COMMAND")

    fna_p = sub.add_parser(
        "fna", help="paint a nucleic-acid FASTA (one pixel per base)",
    )
    _configure_fna(fna_p)
    fna_p.set_defaults(func=paint_cmd.run, command="fna")

    faa_p = sub.add_parser(
        "faa", help="paint a protein FASTA (one pixel per residue)",
    )
    _configure_faa(faa_p)
    faa_p.set_defaults(func=paint_cmd.run, command="faa")

    gc_p = sub.add_parser("gc", help="GC-content heatmap over sliding windows")
    _configure_gc(gc_p)
    gc_p.set_defaults(func=gc_cmd.run, command="gc")

    dp_p = sub.add_parser("dotplot", help="k-mer dot plot comparing two sequences")
    _configure_dotplot(dp_p)
    dp_p.set_defaults(func=compare_cmd.run_dotplot, command="dotplot")

    diff_p = sub.add_parser(
        "diff", help="Needleman-Wunsch alignment diff of two sequences",
    )
    _configure_diff(diff_p)
    diff_p.set_defaults(func=compare_cmd.run_diff, command="diff")

    st_p = sub.add_parser("stacked", help="one row per record from a multi-FASTA")
    _configure_stacked(st_p)
    st_p.set_defaults(func=compare_cmd.run_stacked, command="stacked")

    return p


_FIXED_ALPHABET: dict[str, Alphabet] = {"fna": "nucleic", "faa": "amino", "gc": "nucleic"}


def _alphabet_for_fetch(command: str, accession: str) -> Alphabet:
    fixed = _FIXED_ALPHABET.get(command)
    if fixed is not None:
        return fixed
    return detect_alphabet_from_accession(accession) or "nucleic"


def _resolve_primary(args: argparse.Namespace) -> Path:
    if args.input is not None:
        return Path(args.input)
    alph = _alphabet_for_fetch(args.command, args.accession)
    return fetch_accession(args.accession, alphabet=alph)


def _resolve_secondary(args: argparse.Namespace) -> Path | None:
    input2 = getattr(args, "input2", None)
    accession2 = getattr(args, "accession2", None)
    if input2 is not None:
        return Path(input2)
    if accession2 is not None:
        alph = detect_alphabet_from_accession(accession2) or "nucleic"
        return fetch_accession(accession2, alphabet=alph)
    return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    path = _resolve_primary(args)

    if args.command in ("fna", "faa"):
        alphabet = _FIXED_ALPHABET[args.command]
        return args.func(args, path, alphabet)
    if args.command == "gc":
        return args.func(args, path)
    if args.command in ("dotplot", "diff"):
        path2 = _resolve_secondary(args)
        if path2 is None:
            parser.error(f"{args.command} requires --input2 or --accession2")
        return args.func(args, path, path2)
    if args.command == "stacked":
        return compare_cmd.run_stacked(args, path)
    raise AssertionError(f"unreachable: command={args.command}")


if __name__ == "__main__":
    sys.exit(main())
