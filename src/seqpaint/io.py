from __future__ import annotations

import gzip
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

GZIP_SUFFIXES = (".gz",)
BGZIP_SUFFIXES = (".bgz", ".bgzf")


@dataclass(frozen=True)
class FastaRecord:
    description: str
    sequence: str


def parse_fasta(lines: Iterable[str]) -> Iterator[FastaRecord]:
    """Yield FastaRecord objects from an iterable of FASTA text lines.

    Comments (lines starting with ';') are ignored. A trailing '*' stop
    codon on the final sequence line is stripped. Sequence case is
    preserved here; callers normalize as needed.
    """
    desc: str | None = None
    chunks: list[str] = []
    for raw in lines:
        line = raw.rstrip("\n").rstrip("\r")
        if not line:
            continue
        if line[0] == ";":
            continue
        if line[0] == ">":
            if desc is not None:
                yield FastaRecord(desc, _finalize("".join(chunks)))
            desc = line[1:].strip()
            chunks = []
            continue
        chunks.append(line.strip())
    if desc is not None:
        yield FastaRecord(desc, _finalize("".join(chunks)))


def _finalize(seq: str) -> str:
    if seq.endswith("*"):
        seq = seq[:-1]
    return seq


def _open_text(path: Path) -> TextIO:
    lower = path.name.lower()
    if lower.endswith(GZIP_SUFFIXES):
        return gzip.open(path, "rt")  # type: ignore[return-value]
    if lower.endswith(BGZIP_SUFFIXES):
        try:
            from Bio import bgzf  # type: ignore[import-not-found,import-untyped]
        except ImportError as e:
            raise ImportError(
                "reading .bgz/.bgzf files requires biopython; "
                "install with `pip install 'seqpaint[bgzf]'`"
            ) from e
        return bgzf.open(path, "rt")
    return open(path)


def read_fasta(path: str | Path) -> list[FastaRecord]:
    with _open_text(Path(path)) as f:
        return list(parse_fasta(f))


def read_fasta_stream(f: TextIO) -> Iterator[FastaRecord]:
    return parse_fasta(f)


def iter_fasta(path: str | Path) -> Iterator[FastaRecord]:
    """Yield FastaRecord objects lazily from `path`, without loading all
    records into a list. The file handle is held open for the duration of
    iteration; callers should consume or close promptly.

    Peak memory scales with the largest single record, not total file size —
    a helpful improvement for multi-FASTA inputs with many records. For
    single huge records, the image buffer (width * height * 4 bytes)
    remains the dominant memory cost.
    """
    f = _open_text(Path(path))
    try:
        yield from parse_fasta(f)
    finally:
        f.close()
