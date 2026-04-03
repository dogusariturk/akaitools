"""Plotting utilities for AkaiKKR parsed results."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from matplotlib.figure import Figure

    from akaitools.models import DOSResult, GOResult

try:
    import matplotlib.pyplot as plt
except ImportError:
    print(
        "Plotting requires matplotlib. Install the project dependencies with: pip install .",
        file=sys.stderr,
    )
    raise

# 1 Rydberg in eV — CODATA 2018 (https://physics.nist.gov/cgi-bin/cuu/Value?rydhcev)
_RY_TO_EV: float = 13.605693


def plot_dos(
    result: DOSResult,
    *,
    ef: float = 0.0,
    components: list[int] | None = None,
    spin: str | None = None,
    orbitals: list[str] | None = None,
    energy_unit: str = "Ry",
    figsize: tuple[float, float] = (8, 5),
) -> Figure:
    """Plot density of states curves.

    Args:
        result: Parsed DOS result.
        ef: Fermi energy in Ry, subtracted from the energy axis.
        components: Component indices to plot.  Defaults to all components.
        spin: Spin channel to plot — ``"up"``, ``"down"``, or ``None`` for both.
        orbitals: Which orbital DOS to include, any subset of
            ``["s", "p", "d", "f", "total"]``.  Defaults to ``["total"]``.
        energy_unit: ``"Ry"`` or ``"eV"`` (converts with 1 Ry = 13.6057 eV).
        figsize: Matplotlib figure size ``(width, height)`` in inches.

    Returns:
        The populated Matplotlib figure.
    """
    if orbitals is None:
        orbitals = ["total"]

    comps_to_plot = [
        c
        for c in result.dos_components
        if (components is None or c.component_index in components) and (spin is None or c.spin == spin)
    ]

    fig, ax = plt.subplots(figsize=figsize)

    for comp in comps_to_plot:
        energy = comp.energy - ef
        if energy_unit == "eV":
            energy *= _RY_TO_EV

        for orb in orbitals:
            dos_arr = getattr(comp, orb, None)
            if dos_arr is None:
                continue
            label = f"comp {comp.component_index} ({comp.spin}) - {orb}"
            ax.plot(energy, dos_arr, label=label, lw=1.2)

    ax.axvline(0, color="gray", lw=0.8, ls="--", label="$E_F$")
    ax.set_xlabel(f"Energy ({energy_unit})")
    ax.set_ylabel("DOS (states / Ry / cell)")
    ax.set_title("Density of States")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def plot_dos_spin(
    result: DOSResult,
    *,
    component: int | list[int] | None = None,
    ef: float = 0.0,
    orbital: str = "total",
    energy_unit: str = "Ry",
    figsize: tuple[float, float] = (8, 5),
) -> Figure:
    """Plot spin-resolved DOS with spin-down reflected below zero.

    Args:
        result: Parsed DOS result.
        component: Component index or list of indices to plot.  When ``None``
            (default) the total system DOS is plotted.
        ef: Fermi energy in Ry.
        orbital: Which orbital to plot — ``"total"``, ``"s"``, ``"p"``,
            ``"d"``, or ``"f"``.  Ignored when ``component`` is ``None``.
        energy_unit: ``"Ry"`` or ``"eV"``.
        figsize: Matplotlib figure size ``(width, height)`` in inches.

    Returns:
        The populated Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=figsize)

    if component is None:
        for curve, sign, color, label in [
            (result.total_up, 1, "tab:blue", "spin up (total)"),
            (result.total_down, -1, "tab:red", "spin down (total)"),
        ]:
            if curve is not None:
                energy = curve.energy - ef
                if energy_unit == "eV":
                    energy *= _RY_TO_EV
                dos = sign * curve.values
                ax.plot(energy, dos, color=color, lw=1.2, label=label)
                ax.fill_between(energy, dos, alpha=0.15, color=color)
        title = "Spin-resolved DOS - total"
    else:
        _valid_orbitals = ("s", "p", "d", "f", "total")
        if orbital not in _valid_orbitals:
            raise ValueError(f"Unknown orbital {orbital!r}. Valid choices: {_valid_orbitals}")

        components = [component] if isinstance(component, int) else list(component)
        single = len(components) == 1
        prop_colors = [item["color"] for item in plt.rcParams["axes.prop_cycle"]]

        def _get(idx: int, channel: str) -> tuple[np.ndarray, np.ndarray] | None:
            for c in result.dos_components:
                if c.component_index == idx and c.spin == channel:
                    dos = getattr(c, orbital, None)
                    if dos is None:
                        return None
                    return c.energy - ef, dos
            return None

        for i, comp_idx in enumerate(components):
            up_color = "tab:blue" if single else prop_colors[i % len(prop_colors)]
            down_color = "tab:red" if single else prop_colors[i % len(prop_colors)]

            up = _get(comp_idx, "up")
            if up is not None:
                energy, dos = up
                if energy_unit == "eV":
                    energy *= _RY_TO_EV
                ax.plot(
                    energy,
                    dos,
                    color=up_color,
                    lw=1.2,
                    ls="-",
                    label=f"spin up (comp {comp_idx})" if single else f"comp {comp_idx} \u2191",
                )
                if single:
                    ax.fill_between(energy, dos, alpha=0.15, color=up_color)

            down = _get(comp_idx, "down")
            if down is not None:
                energy, dos = down
                if energy_unit == "eV":
                    energy *= _RY_TO_EV
                ax.plot(
                    energy,
                    -dos,
                    color=down_color,
                    lw=1.2,
                    ls="-" if single else "--",
                    label=f"spin down (comp {comp_idx})" if single else f"comp {comp_idx} \u2193",
                )
                if single:
                    ax.fill_between(energy, -dos, alpha=0.15, color=down_color)

        title = f"Spin-resolved DOS - {orbital}"

    ax.axhline(0, color="black", lw=0.6)
    ax.axvline(0, color="gray", lw=0.8, ls="--", label="$E_F$")
    ax.set_xlabel(f"Energy ({energy_unit})")
    ax.set_ylabel("DOS (states / Ry / cell)")
    ax.set_title(title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def plot_convergence(
    result: GOResult,
    *,
    field: str = "rms_error",
    figsize: tuple[float, float] = (7, 4),
) -> Figure:
    """Plot GO convergence history.

    Args:
        result: Parsed GO result.
        field: Which iteration field to plot — ``"rms_error"``,
            ``"moment"``, or ``"total_energy"``.
        figsize: Matplotlib figure size ``(width, height)`` in inches.

    Returns:
        The populated Matplotlib figure.
    """
    iters = result.iterations
    if not iters:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No iteration data", ha="center", va="center")
        return fig

    x = [it.iteration for it in iters]
    y = [getattr(it, field) for it in iters]

    labels = {
        "rms_error": "log10(RMS error)",
        "moment": "Total moment (uB)",
        "total_energy": "Total energy (Ry)",
    }

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(x, y, lw=1.2, color="tab:blue")
    ax.set_xlabel("Iteration")
    ax.set_ylabel(labels.get(field, field))
    ax.set_title(f"GO convergence - {labels.get(field, field)}")
    if result.converged:
        ax.axvline(x[-1], color="green", ls="--", lw=0.8, label="converged")
        ax.legend(fontsize=8)
    fig.tight_layout()
    return fig
