from pathlib import Path

from seqpaint.gff import parse_gff, read_gff

FIXTURES = Path(__file__).parent / "fixtures"


def test_read_gff_fixture():
    features = read_gff(FIXTURES / "tiny.gff")
    types = [f.type for f in features]
    assert types == ["gene", "CDS", "five_prime_UTR", "three_prime_UTR"]
    gene = features[0]
    assert gene.start == 1 and gene.end == 12
    assert gene.attributes == {"ID": "gene1", "Name": "example"}


def test_parse_skips_comments_and_blanks():
    lines = [
        "##gff-version 3\n",
        "\n",
        "# comment\n",
        "seqA\tx\tgene\t10\t20\t.\t+\t.\tID=g1\n",
    ]
    feats = list(parse_gff(lines))
    assert len(feats) == 1
    assert feats[0].seqid == "seqA"


def test_parse_stops_at_fasta_section():
    lines = [
        "seqA\tx\tgene\t1\t5\t.\t+\t.\tID=g1\n",
        ">seqA\n",
        "ACGT\n",
        "seqB\tx\tgene\t1\t5\t.\t+\t.\tID=g2\n",
    ]
    feats = list(parse_gff(lines))
    assert len(feats) == 1


def test_parse_skips_malformed_rows():
    lines = [
        "only\ttwo\n",
        "seqA\tx\tgene\tnot_a_number\t5\t.\t+\t.\tID=g\n",
        "seqA\tx\tgene\t1\t5\t.\t+\t.\tID=ok\n",
    ]
    feats = list(parse_gff(lines))
    assert len(feats) == 1
    assert feats[0].attributes["ID"] == "ok"
