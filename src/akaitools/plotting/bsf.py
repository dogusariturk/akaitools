"""Bloch spectral function (BSF) plotting for AkaiKKR SPC results."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable

if TYPE_CHECKING:
    import matplotlib.axes
    from matplotlib.figure import Figure

    from akaitools.models import SPCResult, SpectralFunction

from akaitools.errors import InvalidParameterError
from akaitools.plotting.common import plt
from akaitools.plotting.styles import EF_COLOR, STYLE_RC, ZERO_LINE_COLOR
from akaitools.utils import RY_TO_EV

_K_LABEL_SYMBOLS: dict[str, str] = {
    "(0 0 0)": "Γ",
    "(0 1 0)": "H",
    "(1/2 1/2 0)": "N",
    "(1/2 1/2 1/2)": "P",
    "(1 0 0)": "X",
    "(1 1/2 0)": "W",
    "(3/4 3/4 0)": "K",
}


def _format_k_label(label: str) -> str:
    """Map a raw high-symmetry coordinate string to a compact BZ symbol.

    Args:
        label: Raw label from ``KMeshInfo.high_symmetry_indices``
            (e.g. ``"(0 0 0)"``).

    Returns:
        The mapped symbol (e.g. ``"Γ"``), or the raw label unchanged if not recognized.
    """
    return _K_LABEL_SYMBOLS.get(label, label)


def _plot_bsf_channel(
    ax: matplotlib.axes.Axes,
    spectral: SpectralFunction,
    *,
    ef_converted: float,
    use_ev: bool,
    cmap: str,
    vmax: float | None,
    energy_unit: str,
    show_cbar_label: bool = True,
) -> None:
    """Render one spin channel's BSF heatmap onto an axis.

    Args:
        ax: Axis to draw onto.
        spectral: Spectral function for this channel.
        ef_converted: Fermi energy, already converted to the plotted unit.
        use_ev: Whether the energy axis is in eV (``True``) or Ry (``False``).
        cmap: Matplotlib colormap name.
        vmax: Upper color-scale bound, or ``None`` to use the 99.5th percentile.
        energy_unit: ``"Ry"`` or ``"eV"``, used for the y-axis label.
        show_cbar_label: Whether to label this channel's colorbar. Set to
            ``False`` on the left subplot when two channels share the same
            intensity scale, to avoid a redundant label.
    """
    if spectral.data is None:
        ax.text(0.5, 0.5, "No spectral data", ha="center", va="center", transform=ax.transAxes)
        return

    kmesh = spectral.kmesh
    energy = np.linspace(kmesh.energy_min, kmesh.energy_max, kmesh.n_energy)
    if use_ev:
        energy = energy * RY_TO_EV
    energy = energy - ef_converted
    k_axis = np.arange(spectral.data.shape[1])

    vmax_use = vmax if vmax is not None else float(np.percentile(spectral.data, 99.5))
    image = ax.imshow(
        spectral.data,
        origin="lower",
        aspect="auto",
        extent=(k_axis[0], k_axis[-1], energy[0], energy[-1]),
        cmap=cmap,
        vmin=0.0,
        vmax=vmax_use,
    )

    for index in kmesh.high_symmetry_indices:
        ax.axvline(index - 1, color=ZERO_LINE_COLOR, lw=0.5, ls="--", alpha=0.9)
    ax.axhline(0.0, color=EF_COLOR, lw=0.8, ls="--")

    ax.set_xticks([index - 1 for index in kmesh.high_symmetry_indices])
    ax.set_xticklabels([_format_k_label(label) for label in kmesh.high_symmetry_indices.values()])
    ax.set_xlabel("k-path")
    ax.set_ylabel(rf"$E - E_{{\mathrm{{F}}}}$ ({energy_unit})")

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="4.5%", pad=0.05)
    cbar = ax.figure.colorbar(image, cax=cax)
    if show_cbar_label:
        cbar.set_label("BSF intensity")


_SINGLE_PANEL_FIGSIZE: tuple[float, float] = (3.4, 2.6)


def plot_bsf(
    result: SPCResult,
    *,
    spin: str | None = None,
    ef: float = 0.0,
    energy_unit: str = "Ry",
    cmap: str = "YlGnBu",
    vmax: float | None = None,
    figsize: tuple[float, float] | None = None,
) -> Figure:
    """Plot the Bloch spectral function (BSF) as a k-path heatmap.

    Args:
        result: Parsed SPC result.
        spin: Spin channel to plot — ``"up"``, ``"down"``, or ``None`` for
            both (rendered as side-by-side subplots when both channels are
            present).
        ef: Fermi energy in Ry, subtracted from the energy axis.
        energy_unit: ``"Ry"`` or ``"eV"`` (converts with 1 Ry = 13.6057 eV).
        cmap: Matplotlib colormap name for the BSF intensity heatmap.
        vmax: Upper color-scale bound. Defaults to the 99.5th percentile of
            the intensity data when not given, so a few bright outlier
            pixels don't wash out the contrast.
        figsize: Matplotlib figure size ``(width, height)`` in inches.
            Defaults to ``(3.4, 2.6)`` for a single channel, or double that
            width when both channels are rendered side by side.

    Returns:
        The populated Matplotlib figure. A placeholder figure is returned
        (instead of raising) when the requested channel's spectral data is
        unavailable or its k-path was not computed.
    """
    if energy_unit not in ("Ry", "eV"):
        raise InvalidParameterError(f"Unknown energy_unit {energy_unit!r}. Valid choices: ('Ry', 'eV')")
    if spin is not None and spin not in ("up", "down"):
        raise InvalidParameterError(f"Unknown spin {spin!r}. Valid choices: ('up', 'down')")

    channels = [
        (name, sf)
        for name, sf in (("up", result.spectral_up), ("down", result.spectral_down))
        if (spin is None or spin == name) and sf is not None
    ]

    with plt.rc_context(STYLE_RC):
        if not channels:
            fig, ax = plt.subplots(figsize=figsize or _SINGLE_PANEL_FIGSIZE)
            ax.text(0.5, 0.5, "No spectral data", ha="center", va="center")
            return fig

        use_ev = energy_unit == "eV"
        ef_converted = ef * RY_TO_EV if use_ev else ef

        titles = {"up": "Spin up", "down": "Spin down"}
        if len(channels) == 2:
            width, height = figsize or _SINGLE_PANEL_FIGSIZE
            two_panel_figsize = (width, height) if figsize is not None else (width * 2, height)
            fig, axes = plt.subplots(1, 2, figsize=two_panel_figsize, sharey=True)
        else:
            fig, ax = plt.subplots(figsize=figsize or _SINGLE_PANEL_FIGSIZE)
            axes = [ax]

        for i, (channel, spectral) in enumerate(channels):
            ax = axes[i]
            _plot_bsf_channel(
                ax,
                spectral,
                ef_converted=ef_converted,
                use_ev=use_ev,
                cmap=cmap,
                vmax=vmax,
                energy_unit=energy_unit,
                show_cbar_label=not (len(channels) == 2 and i == 0),
            )
            if len(channels) == 2:
                ax.set_title(titles[channel])
                if i > 0:
                    ax.set_ylabel("")

        fig.tight_layout()
    return fig
