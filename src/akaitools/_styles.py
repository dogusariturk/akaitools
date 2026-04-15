"""Shared plot style constants for akaitools."""

from __future__ import annotations

from cycler import cycler

COLORS: list[str] = [
    "#1B6F8A",  # blue-teal
    "#B24A3A",  # brick red
    "#2F7F5F",  # forest green
    "#7C6A4D",  # muted brown
    "#6A5D8F",  # muted violet
    "#A15C7A",  # rose
    "#5F8E9D",  # pale teal
    "#9B7F3F",  # ochre
    "#6F6F6F",  # gray
    "#3F5D53",  # slate green
]

EF_COLOR: str = "#4A4A4A"
ZERO_LINE_COLOR: str = "#9A9A9A"

STYLE_RC: dict = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    "legend.frameon": False,
    "legend.handlelength": 2.0,
    "legend.handletextpad": 0.4,
    "legend.borderpad": 0.2,
    "legend.labelspacing": 0.3,
    "axes.linewidth": 0.8,
    "axes.labelpad": 3,
    "axes.xmargin": 0,
    "axes.ymargin": 0,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "xtick.minor.width": 0.6,
    "ytick.minor.width": 0.6,
    "xtick.major.size": 3.0,
    "ytick.major.size": 3.0,
    "xtick.minor.size": 2.0,
    "ytick.minor.size": 2.0,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "lines.linewidth": 1.2,
    "lines.markersize": 4,
    "figure.figsize": (3.4, 2.6),
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.grid": False,
    "axes.prop_cycle": cycler(color=COLORS),
}
