import pytest

from seqpaint import (
    Palette,
    diff_image,
    dotplot_image,
    needleman_wunsch,
    stacked_image,
)
from seqpaint.canvas import PngCanvas


def test_dotplot_identity_has_main_diagonal():
    seq = "acgtacgtacgtacgt"
    im = dotplot_image(seq, seq, word_size=4, pixel_size=1, max_cells=1000)
    # The main diagonal should be entirely hits.
    for i in range(len(seq) - 4 + 1):
        px = im.getpixel((i, i))
        assert px != (0, 0, 0, 255), f"expected hit at ({i},{i}), got {px}"


def test_dotplot_unrelated_has_few_hits():
    a = "aaaaaaaaaaaaaaaa"
    b = "cccccccccccccccc"
    im = dotplot_image(a, b, word_size=4, pixel_size=1, max_cells=1000)
    # No common 4-mer -> image should be entirely background.
    assert all(
        im.getpixel((x, y)) == (0, 0, 0, 255)
        for x in range(im.size[0])
        for y in range(im.size[1])
    )


def test_dotplot_downsamples_on_max_cells():
    seq = "acgt" * 100  # 400 chars, 397 k-mer starts at k=4
    im = dotplot_image(seq, seq, word_size=4, max_cells=50, pixel_size=1)
    assert im.size[0] <= 50 and im.size[1] <= 50


def test_dotplot_rejects_sequence_shorter_than_word():
    with pytest.raises(ValueError):
        dotplot_image("acg", "acgt", word_size=4)


def test_needleman_wunsch_identity():
    a = "acgtacgt"
    aa, bb = needleman_wunsch(a, a)
    assert aa == a and bb == a


def test_needleman_wunsch_handles_indel():
    aa, bb = needleman_wunsch("acgt", "acgat")
    assert len(aa) == len(bb)
    # Must introduce exactly one gap in aa to account for the extra 'a' in bb.
    assert aa.count("-") == 1
    assert bb.count("-") == 0


def test_diff_image_shape_matches_alignment():
    im = diff_image("acgt", "acgt", pixel_size=2)
    # Alignment length 4, two rows, 2px -> 8x4
    assert im.size == (8, 4)


def test_diff_image_length_cap():
    with pytest.raises(ValueError):
        diff_image("a" * 100, "a" * 100, length_cap=50)


def test_stacked_image_row_per_record():
    palette = Palette.named("default", alphabet="nucleic")
    records = [("r1", "acgt"), ("r2", "acgta"), ("r3", "ac")]
    im = stacked_image(records, palette=palette, pixel_size=3)
    # width = 5 chars * 3 px, height = 3 rows * 3 px
    assert im.size == (15, 9)
    assert isinstance(im, PngCanvas)
