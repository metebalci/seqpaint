from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from seqpaint.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_fna_single_record(tmp_path):
    out = tmp_path / "out.png"
    rc = main(
        [
            "fna",
            "--input", str(FIXTURES / "tiny.fna"),
            "--output", str(out),
            "--pixel-size", "2",
        ]
    )
    assert rc == 0
    assert out.exists()
    with Image.open(out) as im:
        assert im.mode == "RGBA"


def test_fna_multi_mode_separate(tmp_path):
    stem = tmp_path / "out.png"
    rc = main(
        [
            "fna",
            "--input", str(FIXTURES / "multi.fna"),
            "--output", str(stem),
            "--multi-mode", "separate",
        ]
    )
    assert rc == 0
    assert len(sorted(tmp_path.glob("out*.png"))) == 3


def test_fna_multi_mode_combined(tmp_path):
    out = tmp_path / "combined.png"
    rc = main(
        [
            "fna",
            "--input", str(FIXTURES / "multi.fna"),
            "--output", str(out),
            "--multi-mode", "combined",
        ]
    )
    assert rc == 0
    assert out.exists()


def test_faa_single_record(tmp_path):
    out = tmp_path / "prot.png"
    rc = main(
        [
            "faa",
            "--input", str(FIXTURES / "tiny.faa"),
            "--output", str(out),
            "--pixel-size", "3",
        ]
    )
    assert rc == 0


def test_fna_hilbert_is_square(tmp_path):
    out = tmp_path / "hilbert.png"
    rc = main(
        [
            "fna",
            "--input", str(FIXTURES / "tiny.fna"),
            "--output", str(out),
            "--palette", "colorblind-safe",
            "--layout", "hilbert",
        ]
    )
    assert rc == 0
    with Image.open(out) as im:
        assert im.size[0] == im.size[1]


def test_fna_gzipped_input(tmp_path):
    out = tmp_path / "gz.png"
    rc = main(["fna", "--input", str(FIXTURES / "tiny.fna.gz"), "--output", str(out)])
    assert rc == 0


def test_fna_accession_fetch(tmp_path, monkeypatch):
    payload = b">NC_045512.2 fake record\nACGTACGTACGT\n"

    class _Resp:
        def __init__(self, data: bytes) -> None:
            self._buf = BytesIO(data)

        def read(self) -> bytes:
            return self._buf.read()

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(url, timeout=None):
        return _Resp(payload)

    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    out = tmp_path / "acc.png"
    with patch("urllib.request.urlopen", fake_urlopen):
        rc = main(["fna", "--accession", "NC_045512.2", "--output", str(out)])
    assert rc == 0


def test_input_and_accession_mutually_exclusive(tmp_path):
    out = tmp_path / "x.png"
    with pytest.raises(SystemExit):
        main([
            "fna",
            "--input", str(FIXTURES / "tiny.fna"),
            "--accession", "NC_045512.2",
            "--output", str(out),
        ])


def test_fna_annotations(tmp_path):
    out = tmp_path / "annot.png"
    rc = main(
        [
            "fna",
            "--input", str(FIXTURES / "tiny.fna"),
            "--output", str(out),
            "--annotations", str(FIXTURES / "tiny.gff"),
            "--pixel-size", "4",
            "--aspect-ratio", "6", "4",
        ]
    )
    assert rc == 0


def test_fna_annotations_hilbert_rejected(tmp_path):
    out = tmp_path / "bad.png"
    rc = main(
        [
            "fna",
            "--input", str(FIXTURES / "tiny.fna"),
            "--output", str(out),
            "--annotations", str(FIXTURES / "tiny.gff"),
            "--layout", "hilbert",
        ]
    )
    assert rc == 2


def test_fna_kmer(tmp_path):
    out = tmp_path / "kmer.png"
    rc = main(
        [
            "fna",
            "--input", str(FIXTURES / "tiny.fna"),
            "--output", str(out),
            "--kmer", "3",
        ]
    )
    assert rc == 0


def test_gc_command(tmp_path):
    out = tmp_path / "gc.png"
    rc = main(
        [
            "gc",
            "--input", str(FIXTURES / "tiny.fna"),
            "--output", str(out),
            "--window", "4",
            "--step", "2",
            "--pixel-size", "2",
        ]
    )
    assert rc == 0
    with Image.open(out) as im:
        assert im.mode == "RGBA"


def test_kmer_on_faa_rejected(tmp_path):
    """--kmer isn't defined on faa subparser, so argparse rejects it."""
    out = tmp_path / "bad.png"
    with pytest.raises(SystemExit):
        main(
            [
                "faa",
                "--input", str(FIXTURES / "tiny.faa"),
                "--output", str(out),
                "--kmer", "3",
            ]
        )


def test_b_is_on_fna_rejected(tmp_path):
    """--b-is isn't defined on fna subparser, so argparse rejects it."""
    out = tmp_path / "bad.png"
    with pytest.raises(SystemExit):
        main(
            [
                "fna",
                "--input", str(FIXTURES / "tiny.fna"),
                "--output", str(out),
                "--b-is", "d",
            ]
        )


def test_gc_requires_output():
    with pytest.raises(SystemExit):
        main(["gc", "--input", str(FIXTURES / "tiny.fna")])


def test_dotplot_command(tmp_path):
    out = tmp_path / "dp.png"
    rc = main(
        [
            "dotplot",
            "--input", str(FIXTURES / "tiny.fna"),
            "--input2", str(FIXTURES / "tiny.fna"),
            "--output", str(out),
            "--word-size", "4",
            "--pixel-size", "2",
        ]
    )
    assert rc == 0
    assert out.exists()


def test_dotplot_missing_second_input_errors(tmp_path):
    out = tmp_path / "dp.png"
    with pytest.raises(SystemExit):
        main([
            "dotplot",
            "--input", str(FIXTURES / "tiny.fna"),
            "--output", str(out),
        ])


def test_diff_command(tmp_path):
    out = tmp_path / "diff.png"
    rc = main(
        [
            "diff",
            "--input", str(FIXTURES / "tiny.fna"),
            "--input2", str(FIXTURES / "tiny.fna"),
            "--output", str(out),
            "--pixel-size", "2",
        ]
    )
    assert rc == 0


def test_stacked_command(tmp_path):
    out = tmp_path / "stk.png"
    rc = main(
        [
            "stacked",
            "--input", str(FIXTURES / "multi.fna"),
            "--output", str(out),
            "--pixel-size", "3",
        ]
    )
    assert rc == 0
    with Image.open(out) as im:
        assert im.size[1] == 9


def test_unknown_subcommand_errors():
    with pytest.raises(SystemExit):
        main(["nonsense", "--input", str(FIXTURES / "tiny.fna")])


def test_fna_svg_output(tmp_path):
    out = tmp_path / "paint.svg"
    rc = main(
        [
            "fna",
            "--input", str(FIXTURES / "tiny.fna"),
            "--output", str(out),
            "--pixel-size", "4",
        ]
    )
    assert rc == 0
    text = out.read_text()
    assert text.startswith("<svg")
    assert "<rect" in text


def test_fna_html_output_has_tooltip(tmp_path):
    out = tmp_path / "paint.html"
    rc = main(
        [
            "fna",
            "--input", str(FIXTURES / "tiny.fna"),
            "--output", str(out),
            "--pixel-size", "4",
        ]
    )
    assert rc == 0
    text = out.read_text()
    assert "<svg" in text
    assert "SEQ =" in text
    assert "INDEX_MAP" in text


def test_dotplot_svg_output(tmp_path):
    out = tmp_path / "dp.svg"
    rc = main(
        [
            "dotplot",
            "--input", str(FIXTURES / "tiny.fna"),
            "--input2", str(FIXTURES / "tiny.fna"),
            "--output", str(out),
            "--word-size", "4",
        ]
    )
    assert rc == 0
    assert out.read_text().startswith("<svg")


def test_input2_on_fna_unknown(tmp_path):
    """fna doesn't define --input2, so argparse should reject it."""
    out = tmp_path / "bad.png"
    with pytest.raises(SystemExit):
        main([
            "fna",
            "--input", str(FIXTURES / "tiny.fna"),
            "--input2", str(FIXTURES / "tiny.fna"),
            "--output", str(out),
        ])
