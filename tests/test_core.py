import pytest

from seqpaint import Palette, paint, paint_values

NUCLEIC = Palette.named("default", alphabet="nucleic")


def test_paint_default_pixel_size_is_sequence_length_shaped():
    im = paint("acgtacgt" * 4, palette=NUCLEIC)
    assert im.size[0] * im.size[1] >= 32


def test_paint_respects_pixel_size():
    im = paint("acgt", palette=NUCLEIC, pixel_size=4)
    assert im.size == (8, 8)


def test_paint_respects_aspect_ratio():
    im = paint("a" * 24, palette=NUCLEIC, aspect_ratio=(3, 2))
    assert im.size[0] > im.size[1]


def test_paint_accepts_raw_dict_palette():
    palette = {"a": (10, 20, 30, 255), "n": (99, 99, 99, 255)}
    im = paint(
        "ax", palette=palette, pixel_size=1, aspect_ratio=(2, 1),
        bg_color=(0, 0, 0, 255),
    )
    assert im.getpixel((0, 0)) == (10, 20, 30, 255)
    assert im.getpixel((1, 0)) == (99, 99, 99, 255)


def test_paint_with_palette_object():
    pal = Palette(colors={"a": (1, 2, 3, 255)}, fallback=(9, 9, 9, 255))
    im = paint("az", palette=pal, pixel_size=1, aspect_ratio=(2, 1))
    assert im.getpixel((0, 0)) == (1, 2, 3, 255)
    assert im.getpixel((1, 0)) == (9, 9, 9, 255)


def test_paint_rejects_empty_sequence():
    with pytest.raises(ValueError):
        paint("", palette=NUCLEIC)


def test_paint_rejects_invalid_pixel_size():
    with pytest.raises(ValueError):
        paint("acgt", palette=NUCLEIC, pixel_size=0)


def test_paint_rejects_invalid_aspect_ratio():
    with pytest.raises(ValueError):
        paint("acgt", palette=NUCLEIC, aspect_ratio=(0, 1))


def test_paint_values_grayscale():
    im = paint_values([0.0, 0.5, 1.0, 0.25], pixel_size=1, aspect_ratio=(2, 2))
    # 4 values in 2x2 grid -> 2x2 image
    assert im.size == (2, 2)
    # value 0.0 -> black, 1.0 -> white
    assert im.getpixel((0, 0)) == (0, 0, 0, 255)
    # position of 1.0 is index 2 -> raster: (0, 1)
    assert im.getpixel((0, 1)) == (255, 255, 255, 255)


def test_paint_values_rejects_empty():
    with pytest.raises(ValueError):
        paint_values([])
