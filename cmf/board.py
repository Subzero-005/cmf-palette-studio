from PIL import Image, ImageDraw, ImageFont

from .palette import Swatch

WIDTH = 1600
MARGIN = 48
THUMB_H = 260
SWATCH_H = 220
BG = (250, 250, 248)
INK = (30, 30, 32)
MUTED = (110, 110, 115)


def _font(size: int, bold: bool = False):
    candidates = (
        ["Arial Bold.ttf", "DejaVuSans-Bold.ttf", "Helvetica-Bold.ttf"]
        if bold
        else ["Arial.ttf", "DejaVuSans.ttf", "Helvetica.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text_on(rgb) -> tuple:
    r, g, b = rgb
    return INK if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else (245, 245, 245)


def render_board(images: list[Image.Image], palette: list[Swatch], title: str = "CMF Board") -> Image.Image:
    """Lay out reference images and the merged palette as a shareable board."""
    has_images = bool(images)
    height = MARGIN * 2 + 70 + (THUMB_H + MARGIN if has_images else 0) + SWATCH_H + 110
    board = Image.new("RGB", (WIDTH, height), BG)
    draw = ImageDraw.Draw(board)
    draw.text((MARGIN, MARGIN), title, font=_font(40, bold=True), fill=INK)

    y = MARGIN + 70
    if has_images:
        cols = min(len(images), 6)
        cell_w = (WIDTH - MARGIN * 2 - (cols - 1) * 16) // cols
        for i, img in enumerate(images[:cols]):
            thumb = img.convert("RGB")
            thumb.thumbnail((cell_w, THUMB_H))
            x = MARGIN + i * (cell_w + 16) + (cell_w - thumb.width) // 2
            board.paste(thumb, (x, y + (THUMB_H - thumb.height) // 2))
        y += THUMB_H + MARGIN

    if palette:
        # every swatch gets a minimum width so small accent colours stay visible;
        # the remaining space is shared out by how much of the palette each colour covers
        usable = WIDTH - MARGIN * 2
        min_w = min(150, usable // len(palette))
        extra = usable - min_w * len(palette)
        x = MARGIN
        for i, sw in enumerate(palette):
            w = MARGIN + usable - x if i == len(palette) - 1 else min_w + int(extra * sw.share)
            draw.rectangle([x, y, x + w, y + SWATCH_H], fill=sw.rgb)
            fg = _text_on(sw.rgb)
            draw.text((x + 12, y + 12), sw.hex, font=_font(22, bold=True), fill=fg)
            draw.text((x + 12, y + 42), f"{sw.share:.0%}", font=_font(18), fill=fg)
            draw.text((x + 12, y + SWATCH_H + 12), sw.name, font=_font(20, bold=True), fill=INK)
            draw.text((x + 12, y + SWATCH_H + 40), sw.finish_hint, font=_font(16), fill=MUTED)
            x += w
    return board
