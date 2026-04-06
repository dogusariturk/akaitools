"""Shared plot style constants for akaitools."""

from __future__ import annotations

from cycler import cycler

COLORS: list[str] = [
    "#4C9F70",  # green
    "#C76A1E",  # orange
    "#3E78B2",  # blue
    "#8B5E8A",  # muted plum
    "#6E8B3D",  # olive
    "#B24C63",  # rose
    "#5D8AA8",  # steel blue
    "#A47C48",  # tan
    "#6F6F6F",  # gray
    "#2F4F4F",  # slate
]

EF_COLOR: str = "#4A4A4A"
ZERO_LINE_COLOR: str = "#9A9A9A"

STYLE_RC: dict = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 8,
    "axes.labelsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "legend.frameon": False,
    "legend.handlelength": 1.6,
    "legend.handletextpad": 0.4,
    "legend.borderpad": 0.2,
    "legend.labelspacing": 0.3,
    "axes.linewidth": 1.0,
    "axes.labelpad": 3,
    "axes.xmargin": 0,
    "axes.ymargin": 0,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.minor.width": 0.6,
    "ytick.minor.width": 0.6,
    "xtick.major.size": 3.5,
    "ytick.major.size": 3.5,
    "xtick.minor.size": 2.0,
    "ytick.minor.size": 2.0,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "lines.linewidth": 1,
    "lines.markersize": 4,
    "figure.figsize": (3.4, 2.6),
    "figure.dpi": 300,
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "axes.grid": False,
    "axes.prop_cycle": cycler(color=COLORS),
}
