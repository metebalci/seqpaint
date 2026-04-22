import pytest

from seqpaint import kmer_colors, paint_colors


def test_same_kmer_same_color():
    seq = "acgtacgtacgt"
    colors = kmer_colors(seq, k=4)
    # 'acgt' appears at positions 0, 4, 8 -> same color
    assert colors[0] == colors[4] == colors[8]


def test_different_kmers_usually_differ():
    seq = "aaaacccctttt"
    colors = kmer_colors(seq, k=4)
    # Unique 4-mers: aaaa, aaac, aacc, accc, cccc, ccct, cctt, cttt, tttt
    assert colors[0] != colors[4]
    assert colors[0] != colors[8]


def test_kmer_with_n_gets_invalid_color():
    seq = "acgtnnnnacgt"
    colors = kmer_colors(seq, k=3, invalid=(1, 2, 3, 4))
    # Positions 2..7 have a k-mer containing 'n' -> invalid
    for i in (2, 3, 4, 5, 6, 7):
        assert colors[i] == (1, 2, 3, 4)


def test_tail_positions_get_invalid_color():
    seq = "acgt"
    colors = kmer_colors(seq, k=3, invalid=(9, 9, 9, 9))
    # Only positions 0 and 1 have a full 3-mer
    assert colors[2] == (9, 9, 9, 9)
    assert colors[3] == (9, 9, 9, 9)


def test_invalid_k_raises():
    with pytest.raises(ValueError):
        kmer_colors("acgt", k=0)


def test_paint_colors_renders():
    colors = [(10, 20, 30, 255), (40, 50, 60, 255)] * 8
    im = paint_colors(colors, pixel_size=1, aspect_ratio=(4, 4))
    assert im.size == (4, 4)


def test_paint_colors_rejects_empty():
    with pytest.raises(ValueError):
        paint_colors([])
