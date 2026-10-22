from PIL import Image

from cmf import extract_palette, merge_palettes, render_board
from cmf.palette import nearest_name


def two_tone(a, b, split=0.75, size=(100, 100)):
    img = Image.new("RGB", size, b)
    img.paste(Image.new("RGB", (int(size[0] * split), size[1]), a), (0, 0))
    return img


def test_dominant_colour_comes_first():
    palette = extract_palette(two_tone((200, 30, 40), (20, 20, 20)), colours=2)
    assert palette[0].rgb == (200, 30, 40)
    assert abs(palette[0].share - 0.75) < 0.02
    assert abs(sum(s.share for s in palette) - 1) < 1e-6


def test_transparent_pixels_are_ignored():
    img = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    img.paste(Image.new("RGBA", (25, 25), (0, 71, 171, 255)), (0, 0))
    palette = extract_palette(img, colours=3)
    assert len(palette) == 1 and palette[0].rgb == (0, 71, 171)


def test_flat_image_does_not_crash():
    assert len(extract_palette(Image.new("RGB", (40, 40), (10, 10, 10)), colours=6)) == 1


def test_names_and_hex():
    assert nearest_name((198, 32, 41)) == "Racing Red"
    palette = extract_palette(Image.new("RGB", (10, 10), (255, 0, 16)), colours=1)
    assert palette[0].hex == "#FF0010"


def test_merge_keeps_shares_normalised():
    a = extract_palette(two_tone((200, 30, 40), (240, 240, 240)), 2)
    b = extract_palette(two_tone((20, 34, 74), (240, 240, 240)), 2)
    merged = merge_palettes([a, b], colours=3)
    assert len(merged) == 3
    assert abs(sum(s.share for s in merged) - 1) < 1e-6


def test_board_renders():
    img = two_tone((200, 30, 40), (20, 20, 20))
    board = render_board([img], extract_palette(img, 2), "Test")
    assert board.width == 1600 and board.height > 400


def test_small_accent_swatch_is_drawn():
    from cmf.palette import Swatch
    palette = [Swatch((20, 20, 20), 0.95), Swatch((245, 130, 32), 0.05)]
    board = render_board([], palette)
    # the accent must appear on the board even though it covers only 5% of the palette
    assert (245, 130, 32) in {c for _, c in board.getcolors(board.width * board.height)}
