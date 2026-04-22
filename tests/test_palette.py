import pytest

from seqpaint import PALETTE_NAMES, Palette


def test_named_palettes_exist_for_both_alphabets():
    for name in PALETTE_NAMES:
        Palette.named(name, alphabet="nucleic")
        Palette.named(name, alphabet="amino")


def test_named_palettes_are_distinct():
    colors = {
        name: Palette.named(name, alphabet="nucleic").get("a")
        for name in PALETTE_NAMES
    }
    # at least three of the four palettes should disagree on 'a'
    assert len(set(colors.values())) >= 3


def test_overrides_compose():
    p = Palette.named("default", alphabet="nucleic")
    p2 = p.with_overrides({"a": (1, 2, 3, 4)})
    assert p2.get("a") == (1, 2, 3, 4)
    # original is untouched (frozen dataclass)
    assert p.get("a") != (1, 2, 3, 4)


def test_fallback_used_for_unknown_keys():
    p = Palette(colors={"a": (1, 1, 1, 255)}, fallback=(7, 7, 7, 255))
    assert p.get("z") == (7, 7, 7, 255)


def test_unknown_palette_name_raises():
    with pytest.raises(ValueError):
        Palette.named("does-not-exist", alphabet="nucleic")
