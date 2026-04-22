from __future__ import annotations

import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Literal

EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

Alphabet = Literal["nucleic", "amino"]

_DB_FOR_ALPHABET: dict[str, str] = {
    "nucleic": "nuccore",
    "amino": "protein",
}

_ACCESSION_RE = re.compile(r"^[A-Za-z0-9._]+$")


def cache_dir() -> Path:
    root = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    d = Path(root) / "seqpaint"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fetch_accession(
    accession: str,
    alphabet: Alphabet = "nucleic",
    *,
    cache: Path | None = None,
    force: bool = False,
) -> Path:
    """Download a FASTA for an NCBI accession and return the cached path.

    Uses E-utilities efetch. Raises ValueError for malformed accessions,
    urllib.error.URLError for network failures.
    """
    if not _ACCESSION_RE.match(accession):
        raise ValueError(f"invalid accession {accession!r}")
    if alphabet not in _DB_FOR_ALPHABET:
        raise ValueError(f"unknown alphabet {alphabet!r}")

    dest_root = cache if cache is not None else cache_dir()
    dest_root.mkdir(parents=True, exist_ok=True)
    suffix = ".fna" if alphabet == "nucleic" else ".faa"
    dest = dest_root / f"{accession}{suffix}"

    if dest.exists() and not force:
        return dest

    params = {
        "db": _DB_FOR_ALPHABET[alphabet],
        "id": accession,
        "rettype": "fasta",
        "retmode": "text",
    }
    url = f"{EFETCH_URL}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310
        data = resp.read()
    if not data or not data.lstrip().startswith(b">"):
        raise ValueError(
            f"efetch returned no FASTA record for {accession!r} (db={params['db']})"
        )
    dest.write_bytes(data)
    return dest
