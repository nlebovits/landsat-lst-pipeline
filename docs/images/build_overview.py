"""Build docs/images/overview.png, the global map on the homepage.

The collection's own thumbnail is 480 by 160 pixels, which blurs at the width
of the page. This script reads the smallest internal overview of every
published `lst_p95` COG over HTTP, places each 5-degree tile on a 5 pixels per
degree grid from 60 S to 60 N, and colors it with magma. Nodata stays
transparent, so the map sits on either color scheme.

    uv run --group docs python docs/images/build_overview.py

It reads 769 small overviews and takes about two minutes on a home connection.
"""

from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import matplotlib as mpl
import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.errors import RasterioIOError

REPO = Path(__file__).resolve().parents[2]
COLLECTION_DIR = REPO / "catalog" / "lst-p95-2021-2025"
BASE_URL = "https://data.source.coop/nlebovits/landsat-lst/lst-p95-2021-2025"
OUT = Path(__file__).resolve().parent / "overview.png"

PX_PER_DEG = 5
TILE_DEG = 5
TILE_PX = PX_PER_DEG * TILE_DEG
WIDTH, HEIGHT = 360 * PX_PER_DEG, 120 * PX_PER_DEG  # 180 W to 180 E, 60 N to 60 S

TILE_ID = re.compile(r"^([NS])(\d{2})([EW])(\d{3})$")


def tile_origin(tile: str) -> tuple[int, int]:
    """Return the row and column of a tile's top-left pixel on the grid."""
    match = TILE_ID.match(tile)
    assert match, tile
    ns, lat, ew, lon = match.groups()
    north = int(lat) if ns == "N" else -int(lat)
    west = int(lon) if ew == "E" else -int(lon)
    return (60 - north) * PX_PER_DEG, (west + 180) * PX_PER_DEG


def read_tile(tile: str, attempts: int = 4) -> tuple[str, np.ndarray]:
    """Read one tile's temperature in degrees Celsius at TILE_PX square.

    A burst of parallel opens sometimes gets a transient error page back,
    which GDAL reports as an unrecognized format, so each read retries.
    """
    for attempt in range(attempts):
        try:
            with rasterio.open(f"{BASE_URL}/{tile}/lst_p95.tif") as src:
                dn = src.read(
                    1, out_shape=(TILE_PX, TILE_PX), resampling=Resampling.average
                )
                celsius = dn * src.scales[0] + src.offsets[0]
                return tile, np.where(dn == 0, np.nan, celsius)
        except RasterioIOError:
            if attempt == attempts - 1:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def main() -> None:
    tiles = sorted(p.name for p in COLLECTION_DIR.iterdir() if TILE_ID.match(p.name))
    grid = np.full((HEIGHT, WIDTH), np.nan, dtype="float32")
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
        with ThreadPoolExecutor(max_workers=8) as pool:
            for tile, values in pool.map(read_tile, tiles):
                row, col = tile_origin(tile)
                grid[row : row + TILE_PX, col : col + TILE_PX] = values

    low, high = np.nanpercentile(grid, [2, 98])
    scaled = np.clip((grid - low) / (high - low), 0, 1)
    rgba = mpl.colormaps["magma"](np.nan_to_num(scaled), bytes=True)
    rgba[np.isnan(grid), 3] = 0
    # A 256-color palette keeps the file under the 500 KB limit. Magma has
    # 256 colors and nodata needs one transparent entry. The quantizer merges
    # a few neighboring magma steps, which differ by less than the eye sees.
    image = Image.fromarray(rgba, mode="RGBA").quantize(
        colors=256, method=Image.Quantize.FASTOCTREE
    )
    image.save(OUT, optimize=True)
    print(f"{len(tiles)} tiles, stretch {low:.1f} to {high:.1f} C, wrote {OUT}")


if __name__ == "__main__":
    main()
