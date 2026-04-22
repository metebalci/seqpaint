from __future__ import annotations

from pathlib import Path
from typing import Literal

Alphabet = Literal["nucleic", "amino"]

_NUCLEIC_EXTS = {".fna", ".ffn", ".frn"}
_AMINO_EXTS = {".faa"}

# NCBI accession prefixes (loose but useful).
_AMINO_PREFIXES = ("np_", "yp_", "xp_", "wp_", "ap_", "zp_")
_NUCLEIC_PREFIXES = ("nc_", "nm_", "nr_", "xm_", "xr_", "nt_", "nw_", "ng_")

_NUCLEIC_CHARS = set("acgtun-*")


def detect_alphabet_from_path(path: Path) -> Alphabet | None:
    """Guess alphabet from filename extension, ignoring .gz/.bgz/.bgzf."""
    suffixes = [s.lower() for s in path.suffixes]
    meaningful = [s for s in suffixes if s not in (".gz", ".bgz", ".bgzf")]
    if not meaningful:
        return None
    ext = meaningful[-1]
    if ext in _NUCLEIC_EXTS:
        return "nucleic"
    if ext in _AMINO_EXTS:
        return "amino"
    return None


def detect_alphabet_from_accession(accession: str) -> Alphabet | None:
    low = accession.lower()
    if low.startswith(_AMINO_PREFIXES):
        return "amino"
    if low.startswith(_NUCLEIC_PREFIXES):
        return "nucleic"
    return None


def detect_alphabet_from_sequence(seq: str, sniff_chars: int = 200) -> Alphabet:
    """Content sniff: nucleic iff (almost) every char is ACGTUN/-/*."""
    sample = seq[:sniff_chars].lower()
    if not sample:
        return "nucleic"
    non_nucleic = sum(1 for c in sample if c not in _NUCLEIC_CHARS)
    # Small tolerance: real FASTA can have stray whitespace / rare codes.
    return "amino" if non_nucleic > max(2, len(sample) // 20) else "nucleic"
