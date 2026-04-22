from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Feature:
    seqid: str
    type: str
    start: int  # 1-based, inclusive
    end: int  # 1-based, inclusive
    strand: str
    attributes: dict[str, str]


def parse_gff(lines: Iterable[str]) -> Iterator[Feature]:
    """Yield Feature objects from a GFF3 iterable.

    Ignores comment and blank lines. Stops at the FASTA section marker
    (a line beginning with '>'). Rows with fewer than 8 fields are
    silently skipped.
    """
    for raw in lines:
        line = raw.rstrip("\n").rstrip("\r")
        if not line or line.startswith("#"):
            continue
        if line.startswith(">"):
            return
        parts = line.split("\t")
        if len(parts) < 8:
            continue
        try:
            start = int(parts[3])
            end = int(parts[4])
        except ValueError:
            continue
        attrs: dict[str, str] = {}
        if len(parts) >= 9:
            for kv in parts[8].split(";"):
                kv = kv.strip()
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    attrs[k.strip()] = v.strip()
        yield Feature(
            seqid=parts[0],
            type=parts[2],
            start=start,
            end=end,
            strand=parts[6],
            attributes=attrs,
        )


def read_gff(path: str | Path) -> list[Feature]:
    with open(path) as f:
        return list(parse_gff(f))
