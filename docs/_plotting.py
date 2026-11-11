"""Shared figure style for the tutorials on this site.

A tutorial imports this module, calls `apply_style()` once, and draws every
figure with the helpers below. The helpers fix the parts a reader compares
across figures: the typeface, the ink colors, the colormap for each variable,
the dimmed imagery under a map, and the scale bar and north arrow.

Maps take an axes in one of two coordinate systems. Pass `crs="EPSG:4326"` for
an axes in longitude and latitude, and the helpers correct the aspect ratio and
the scale bar for the latitude of the map. Pass a projected CRS in metres for
anything else.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import contextily as cx
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib_scalebar.scalebar import ScaleBar

# Ink and chrome, light mode. The figures render once, to PNG, on a white page.
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#ffffff"

# Categorical slots, validated as a set of three for every pair under
# colour-vision-deficiency simulation (worst pair delta E 9.2, OKLab x100).
URBAN_CLASS_COLORS = {
    "urbana": "#2a78d6",
    "periurbana": "#eb6834",
    "urbano en ruralidad": "#1baf7a",
}
URBAN_CLASS_LABELS = {
    "urbana": "Urban",
    "periurbana": "Peri-urban",
    "urbano en ruralidad": "Rural settlement",
}

# Emissions scenarios: low to high reads cool to warm, as in IPCC figures.
# Validated as a set of three for every pair (worst CVD delta E 22.7).
SCENARIO_COLORS = {
    "historical": INK_SECONDARY,
    "ssp126": "#2a78d6",
    "ssp245": "#eda100",
    "ssp585": "#c0392b",
}
SCENARIO_LABELS = {
    "historical": "Historical",
    "ssp126": "SSP1-2.6",
    "ssp245": "SSP2-4.5",
    "ssp585": "SSP5-8.5",
}

# One sequential colormap per variable, the same in every figure.
CMAP_LST = "magma"
CMAP_CANOPY = "Greens"
CMAP_BUILDINGS = "Purples"
CMAP_POPULATION = "Blues"
CMAP_OBSERVATIONS = "cividis"

HOTSPOT_COLOR = "#d3436e"  # magma at 0.6, for hotspot pixels over imagery

FONT_FAMILIES = ["IBM Plex Sans", "Inter", "Source Sans 3", "DejaVu Sans"]

# The PNG resolution. 110 dots per inch keeps a full-width map with an imagery
# basemap under 500 KB while staying sharp on a standard display.
DPI = 110

ESRI_IMAGERY = cx.providers.Esri.WorldImagery
IMAGERY_CREDIT = "Imagery: Esri, Maxar, Earthstar Geographics"

METRES_PER_DEGREE = 111_320.0


def apply_style() -> None:
    """Set the matplotlib defaults every tutorial figure shares."""
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": FONT_FAMILIES,
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.titleweight": "semibold",
            "axes.titlelocation": "left",
            "axes.titlepad": 8,
            "axes.labelsize": 9.5,
            "axes.labelcolor": INK_SECONDARY,
            "axes.edgecolor": BASELINE,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "axes.facecolor": SURFACE,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelcolor": INK_SECONDARY,
            "ytick.labelcolor": INK_SECONDARY,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "legend.frameon": False,
            "legend.fontsize": 8.5,
            "figure.facecolor": SURFACE,
            "figure.dpi": DPI,
            "savefig.dpi": DPI,
            "figure.titlesize": 12.5,
            "figure.titleweight": "semibold",
            "figure.constrained_layout.use": True,
            "text.color": INK,
            "image.interpolation": "nearest",
        }
    )


def suptitle(fig: plt.Figure, text: str, subtitle: str | None = None) -> None:
    """Title a figure with its takeaway, left-aligned, and an optional subtitle."""
    fig.suptitle(text, x=0.01, ha="left", fontsize=12.5, fontweight="semibold")
    if subtitle:
        fig.text(
            0.01,
            1.0,
            subtitle,
            ha="left",
            va="bottom",
            fontsize=9.5,
            color=INK_SECONDARY,
            transform=fig.transSubfigure,
        )


def _central_latitude(ax: plt.Axes) -> float:
    lo, hi = ax.get_ylim()
    return (lo + hi) / 2.0


def map_axes(ax: plt.Axes, crs: str = "EPSG:4326") -> None:
    """Hide ticks and spines, and fix the aspect ratio for the map's CRS."""
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    if crs == "EPSG:4326":
        ax.set_aspect(1.0 / math.cos(math.radians(_central_latitude(ax))))
    else:
        ax.set_aspect("equal")


def frame(
    ax: plt.Axes,
    bounds: Sequence[float],
    margin: float = 0.04,
    crs: str = "EPSG:4326",
) -> None:
    """Frame the axes on (minx, miny, maxx, maxy) plus a margin, then style it."""
    minx, miny, maxx, maxy = bounds
    pad = margin * max(maxx - minx, maxy - miny)
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)
    map_axes(ax, crs)


def _to_grey(img: np.ndarray, dim: float, levels: int) -> np.ndarray:
    rgb = img[..., :3].astype("float32") / 255.0
    grey = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype="float32")
    # A few grey levels keep the imagery legible and let the PNG compress.
    grey = np.round(grey * levels) / levels
    grey = grey * (1.0 - dim) + dim
    out = np.dstack([grey, grey, grey, np.ones_like(grey)])
    if img.shape[-1] == 4:
        out[..., 3] = img[..., 3] / 255.0
    return out


def basemap(
    ax: plt.Axes,
    crs: str = "EPSG:4326",
    zoom: int | str = "auto",
    dim: float = 0.55,
    credit: bool = True,
    levels: int = 12,
) -> None:
    """Draw Esri World Imagery in greyscale, blended toward white, under the axes.

    Call it after the axes limits are final. `dim` is the share of white mixed
    into the grey image: 0 keeps the full tonal range, 1 is a blank page.
    `levels` is the number of grey steps the image keeps.
    """
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    geographic = crs == "EPSG:4326"
    img, extent = cx.bounds2img(
        minx, miny, maxx, maxy, zoom=zoom, source=ESRI_IMAGERY, ll=geographic
    )
    if crs != "EPSG:3857":
        img, extent = cx.warp_tiles(img, extent, t_crs=crs)
    ax.imshow(
        _to_grey(img, dim, levels),
        extent=extent,
        zorder=0,
        interpolation="nearest",
        origin="upper",
    )
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    if credit:
        ax.text(
            0.995,
            0.005,
            IMAGERY_CREDIT,
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=6.5,
            color=INK_SECONDARY,
            zorder=10,
        )


def scalebar(
    ax: plt.Axes, crs: str = "EPSG:4326", location: str = "lower left"
) -> None:
    """Add a metric scale bar that is correct at the map's central latitude."""
    if crs == "EPSG:4326":
        dx = METRES_PER_DEGREE * math.cos(math.radians(_central_latitude(ax)))
    elif crs == "EPSG:3857":
        dx = math.cos(math.radians(_central_latitude_3857(ax)))
    else:
        dx = 1.0
    ax.add_artist(
        ScaleBar(
            dx,
            units="m",
            location=location,
            length_fraction=0.22,
            box_color=SURFACE,
            box_alpha=0.75,
            color=INK,
            font_properties={"size": 8},
            scale_loc="top",
            border_pad=0.6,
            rotation="horizontal-only",
        )
    )


def _central_latitude_3857(ax: plt.Axes) -> float:
    y = _central_latitude(ax)
    return math.degrees(2.0 * math.atan(math.exp(y / 6_378_137.0)) - math.pi / 2.0)


def north_arrow(
    ax: plt.Axes, x: float = 0.965, y: float = 0.9, size: float = 0.07
) -> None:
    """Draw a small north arrow in axes coordinates."""
    ax.annotate(
        "N",
        xy=(x, y),
        xytext=(x, y - size),
        xycoords="axes fraction",
        ha="center",
        va="center",
        fontsize=8.5,
        fontweight="semibold",
        color=INK,
        arrowprops={
            "arrowstyle": "-|>",
            "color": INK,
            "lw": 1.0,
            "shrinkA": 5,
            "shrinkB": 0,
        },
        zorder=10,
    )


def colorbar(
    ax: plt.Axes,
    mappable: mpl.cm.ScalarMappable,
    label: str,
    width: float = 0.42,
    loc: str = "lower right",
    ticks: Sequence[float] | None = None,
    extend: str = "neither",
) -> mpl.colorbar.Colorbar:
    """Draw a horizontal colorbar with units inside a corner of a map axes."""
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes

    cax = inset_axes(
        ax,
        width=f"{width * 100:.0f}%",
        height="3%",
        loc=loc,
        borderpad=2.2,
    )
    bar = ax.figure.colorbar(
        mappable, cax=cax, orientation="horizontal", ticks=ticks, extend=extend
    )
    bar.outline.set_visible(False)
    bar.ax.tick_params(labelsize=8, length=2, color=MUTED)
    bar.ax.xaxis.set_label_position("top")
    bar.set_label(label, fontsize=8.5, color=INK, labelpad=3)
    cax.patch.set_alpha(0.0)
    return bar


def colorbar_below(
    ax: plt.Axes,
    mappable: mpl.cm.ScalarMappable,
    label: str,
    ticks: Sequence[float] | None = None,
    extend: str = "neither",
    fraction: float = 0.05,
) -> mpl.colorbar.Colorbar:
    """Draw a horizontal colorbar with units under an axes."""
    bar = ax.figure.colorbar(
        mappable,
        ax=ax,
        orientation="horizontal",
        fraction=fraction,
        pad=0.02,
        aspect=40,
        shrink=0.7,
        ticks=ticks,
        extend=extend,
    )
    bar.outline.set_visible(False)
    bar.ax.tick_params(labelsize=8, length=2, color=MUTED)
    bar.set_label(label, fontsize=8.5, color=INK, labelpad=3)
    return bar


def single_color_cmap(color: str) -> ListedColormap:
    """Return a one-entry colormap, for drawing a boolean mask in one color."""
    return ListedColormap([color])


def legend_patch(color: str, label: str, alpha: float = 1.0) -> mpl.patches.Patch:
    """Return a filled square legend entry."""
    return mpl.patches.Patch(
        facecolor=color, edgecolor="none", alpha=alpha, label=label
    )


def legend_line(color: str, label: str, width: float = 1.2) -> mpl.lines.Line2D:
    """Return an outline legend entry."""
    return mpl.lines.Line2D([], [], color=color, lw=width, label=label)
