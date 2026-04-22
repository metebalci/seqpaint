from io import BytesIO
from unittest.mock import patch

import pytest

from seqpaint.fetch import fetch_accession


def _fake_urlopen(payload: bytes):
    class _Resp:
        def __init__(self, data: bytes) -> None:
            self._buf = BytesIO(data)

        def read(self) -> bytes:
            return self._buf.read()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _factory(url, timeout=None):
        _factory.last_url = url  # type: ignore[attr-defined]
        return _Resp(payload)

    return _factory


def test_fetch_writes_cache(tmp_path):
    payload = b">NC_045512.2 fake record\nACGT\n"
    fake = _fake_urlopen(payload)
    with patch("urllib.request.urlopen", fake):
        p = fetch_accession("NC_045512.2", cache=tmp_path)
    assert p.exists()
    assert p.read_bytes() == payload
    assert "db=nuccore" in fake.last_url  # type: ignore[attr-defined]
    assert "id=NC_045512.2" in fake.last_url  # type: ignore[attr-defined]


def test_fetch_reuses_cache(tmp_path):
    payload = b">X fake\nACGT\n"
    dest = tmp_path / "X.fna"
    dest.write_bytes(payload)
    with patch("urllib.request.urlopen", side_effect=AssertionError("should not call")):
        p = fetch_accession("X", cache=tmp_path)
    assert p == dest


def test_fetch_amino_uses_protein_db(tmp_path):
    payload = b">YP_009724389.1 fake\nMKT\n"
    fake = _fake_urlopen(payload)
    with patch("urllib.request.urlopen", fake):
        fetch_accession("YP_009724389.1", alphabet="amino", cache=tmp_path)
    assert "db=protein" in fake.last_url  # type: ignore[attr-defined]


def test_fetch_rejects_bad_accession(tmp_path):
    with pytest.raises(ValueError):
        fetch_accession("has spaces", cache=tmp_path)


def test_fetch_rejects_empty_response(tmp_path):
    fake = _fake_urlopen(b"")
    with patch("urllib.request.urlopen", fake), pytest.raises(ValueError):
        fetch_accession("NC_000000.0", cache=tmp_path)
