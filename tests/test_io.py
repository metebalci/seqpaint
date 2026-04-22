from pathlib import Path

from seqpaint.io import iter_fasta, parse_fasta, read_fasta

FIXTURES = Path(__file__).parent / "fixtures"


def test_single_record():
    records = read_fasta(FIXTURES / "tiny.fna")
    assert len(records) == 1
    assert records[0].description == "tiny-test-seq sample nucleic acid"
    assert records[0].sequence == "ACGTACGTACGTACGTNNNACGTA"


def test_multi_record():
    records = read_fasta(FIXTURES / "multi.fna")
    assert [r.description.split()[0] for r in records] == ["rec1", "rec2", "rec3"]
    assert records[0].sequence == "ACGT"
    assert records[1].sequence == "TTTTAAAA"
    assert records[2].sequence == "GGCC"


def test_comments_are_skipped():
    records = read_fasta(FIXTURES / "with_comments.fna")
    assert len(records) == 1
    assert records[0].sequence == "ACGTACGT"


def test_trailing_star_stripped():
    records = read_fasta(FIXTURES / "tiny.faa")
    assert records[0].sequence == "MKTAYIAKQRQISFVKSHFS"


def test_parse_fasta_from_iterable():
    lines = [">a\n", "AA\n", "CC\n", ">b\n", "GG\n"]
    result = list(parse_fasta(lines))
    assert [r.description for r in result] == ["a", "b"]
    assert [r.sequence for r in result] == ["AACC", "GG"]


def test_empty_input_yields_nothing():
    assert list(parse_fasta([])) == []
    assert list(parse_fasta(["; only a comment\n"])) == []


def test_gzipped_fasta_is_read_transparently():
    records = read_fasta(FIXTURES / "tiny.fna.gz")
    assert len(records) == 1
    assert records[0].sequence == "ACGTACGTACGTACGTNNNACGTA"


def test_iter_fasta_yields_records_lazily():
    records = list(iter_fasta(FIXTURES / "multi.fna"))
    assert [r.description.split()[0] for r in records] == ["rec1", "rec2", "rec3"]


def test_bgz_without_biopython_raises_clearly(tmp_path, monkeypatch):
    import builtins

    stub = tmp_path / "stub.bgz"
    stub.write_bytes(b"irrelevant")

    real_import = builtins.__import__

    def deny_bio(name, *a, **kw):
        if name == "Bio" or name.startswith("Bio."):
            raise ImportError("biopython not installed")
        return real_import(name, *a, **kw)

    import pytest

    monkeypatch.setattr(builtins, "__import__", deny_bio)
    with pytest.raises(ImportError, match="biopython"):
        read_fasta(stub)
