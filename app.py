import json
import tempfile
from pathlib import Path

import gradio as gr
from PIL import Image

from cmf import extract_palette, merge_palettes, render_board


def build_board(files, colours_per_image, board_colours, title):
    if not files:
        raise gr.Error("Upload at least one reference image.")
    images = [Image.open(f if isinstance(f, str) else f.name) for f in files]
    palettes = [extract_palette(img, int(colours_per_image)) for img in images]
    palette = merge_palettes(palettes, int(board_colours))
    board = render_board(images, palette, title or "CMF Board")

    out_dir = Path(tempfile.mkdtemp(prefix="cmf_"))
    png_path, pdf_path, json_path = out_dir / "cmf_board.png", out_dir / "cmf_board.pdf", out_dir / "palette.json"
    board.save(png_path)
    board.save(pdf_path, "PDF", resolution=150)
    json_path.write_text(json.dumps([s.as_dict() for s in palette], indent=2))

    table = [[s.hex, s.name, f"{s.share:.1%}", s.finish_hint] for s in palette]
    return board, table, [str(png_path), str(pdf_path), str(json_path)]


with gr.Blocks(title="CMF Palette Studio") as demo:
    gr.Markdown(
        "# CMF Palette Studio\n"
        "Drop in reference photos (competitor products, mood images, material samples) "
        "and get a ready-to-share colour board with named swatches and finish hints."
    )
    with gr.Row():
        with gr.Column(scale=1):
            files = gr.File(label="Reference images", file_count="multiple", file_types=["image"])
            title = gr.Textbox(label="Board title", value="CMF Board")
            colours_per_image = gr.Slider(2, 10, value=5, step=1, label="Colours per image")
            board_colours = gr.Slider(3, 10, value=6, step=1, label="Colours on board")
            run = gr.Button("Build board", variant="primary")
        with gr.Column(scale=2):
            board = gr.Image(label="Board", type="pil")
            table = gr.Dataframe(headers=["Hex", "Name", "Share", "Finish hint"], label="Palette")
            downloads = gr.File(label="Download (PNG / PDF / JSON)", file_count="multiple")
    run.click(build_board, [files, colours_per_image, board_colours, title], [board, table, downloads])

if __name__ == "__main__":
    demo.launch()
