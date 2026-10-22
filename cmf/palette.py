from dataclasses import dataclass

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

from .names import NAMED_COLOURS

_SAMPLE_SIZE = 160  # images are shrunk to this before clustering; plenty for colour
_NAME_KEYS = list(NAMED_COLOURS)
_NAME_RGB = np.array([NAMED_COLOURS[k] for k in _NAME_KEYS], dtype=float)


@dataclass
class Swatch:
    rgb: tuple
    share: float  # fraction of pixels in this cluster, 0..1

    @property
    def hex(self) -> str:
        return "#{:02X}{:02X}{:02X}".format(*self.rgb)

    @property
    def name(self) -> str:
        return nearest_name(self.rgb)

    @property
    def finish_hint(self) -> str:
        """Rough finish suggestion from lightness and saturation."""
        r, g, b = (c / 255 for c in self.rgb)
        hi, lo = max(r, g, b), min(r, g, b)
        lightness = (hi + lo) / 2
        saturation = 0 if hi == lo else (hi - lo) / (1 - abs(2 * lightness - 1))
        if saturation < 0.12 and 0.35 < lightness < 0.8:
            return "metallic / satin"
        if lightness < 0.2:
            return "gloss or matte black"
        if saturation > 0.6:
            return "gloss accent"
        return "matte / textured"

    def as_dict(self) -> dict:
        return {
            "hex": self.hex,
            "rgb": list(self.rgb),
            "name": self.name,
            "share": round(self.share, 4),
            "finish_hint": self.finish_hint,
        }


def nearest_name(rgb) -> str:
    distances = np.linalg.norm(_NAME_RGB - np.array(rgb, dtype=float), axis=1)
    return _NAME_KEYS[int(distances.argmin())]


def _pixels(image: Image.Image) -> np.ndarray:
    image = image.convert("RGBA")
    image.thumbnail((_SAMPLE_SIZE, _SAMPLE_SIZE))
    data = np.asarray(image).reshape(-1, 4)
    # ignore transparent pixels so cut-out product shots don't add fake black/white
    return data[data[:, 3] > 128][:, :3].astype(float)


def extract_palette(image: Image.Image, colours: int = 6, seed: int = 0) -> list[Swatch]:
    """Return the dominant colours of an image, largest share first."""
    pixels = _pixels(image)
    if len(pixels) == 0:
        return []
    colours = max(1, min(colours, len(np.unique(pixels, axis=0))))
    model = KMeans(n_clusters=colours, n_init=4, random_state=seed).fit(pixels)
    counts = np.bincount(model.labels_, minlength=colours)
    swatches = [
        Swatch(tuple(int(round(c)) for c in centre), count / counts.sum())
        for centre, count in zip(model.cluster_centers_, counts)
    ]
    return sorted(swatches, key=lambda s: s.share, reverse=True)


def merge_palettes(palettes: list[list[Swatch]], colours: int = 8, seed: int = 0) -> list[Swatch]:
    """Combine per-image palettes into one board palette, weighted by share."""
    swatches = [s for palette in palettes for s in palette]
    if not swatches:
        return []
    if len(swatches) <= colours:
        total = sum(s.share for s in swatches)
        return sorted((Swatch(s.rgb, s.share / total) for s in swatches), key=lambda s: s.share, reverse=True)

    points = np.array([s.rgb for s in swatches], dtype=float)
    weights = np.array([s.share for s in swatches])
    model = KMeans(n_clusters=colours, n_init=4, random_state=seed).fit(points, sample_weight=weights)
    shares = np.bincount(model.labels_, weights=weights, minlength=colours)
    merged = [
        Swatch(tuple(int(round(c)) for c in centre), share / shares.sum())
        for centre, share in zip(model.cluster_centers_, shares)
        if share > 0
    ]
    return sorted(merged, key=lambda s: s.share, reverse=True)
