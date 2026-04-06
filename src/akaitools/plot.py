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
    from matplotlib.ticker import ScalarFormatter
except ImportError:
    print(
        "Plotting requires matplotlib. Install the project dependencies with: pip install .",
        file=sys.stderr,
    )
    raise

from akaitools._styles import (
    COLORS,
    EF_COLOR,
    STYLE_RC,
    ZERO_LINE_COLOR,
)

# 1 Rydberg in eV — CODATA 2018 (https://physics.nist.gov/cgi-bin/cuu/Value?rydhcev)
_RY_TO_EV: float = 13.605693


def _convert_energy(energy: np.ndarray, energy_unit: str) -> np.ndarray:
    """Convert an energy array from Ry to the requested unit."""
    if energy_unit == "eV":
        return energy * _RY_TO_EV
    return energy


def _convert_dos(values: np.ndarray, energy_unit: str) -> np.ndarray:
    """Convert DOS from states/Ry to states/{unit} while preserving area."""
    if energy_unit == "eV":
        return values / _RY_TO_EV
    return values


def _scientific_mathtext_formatter() -> ScalarFormatter:
    """Return a scalar formatter with 10^n math text and no additive offset."""
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_useOffset(False)
    return formatter


def plot_dos(
    result: DOSResult,
    *,
    ef: float = 0.0,
    components: list[int] | None = None,
    system_total: bool = True,
    spin: str | None = None,
    orbitals: list[str] | None = None,
    energy_unit: str = "Ry",
    figsize: tuple[float, float] = (3.4, 2.6),
) -> Figure:
    """Plot density of states curves.

    Args:
        result: Parsed DOS result.
        ef: Fermi energy in Ry, subtracted from the energy axis.
        components: Component indices to plot.  Defaults to all components.
        system_total: Add the total system DOS on top of the component curves.
        spin: Spin channel to plot — ``"up"``, ``"down"``, or ``None`` for both.
        orbitals: Which orbital DOS to include, any subset of
            ``["s", "p", "d", "f", "total"]``.  Defaults to ``["total"]``.
            Pass ``[]`` to hide component curves and show only ``system_total``.
        energy_unit: ``"Ry"`` or ``"eV"`` (converts with 1 Ry = 13.6057 eV).
        figsize: Matplotlib figure size ``(width, height)`` in inches.

    Returns:
        The populated Matplotlib figure.
    """
    if energy_unit not in ("Ry", "eV"):
        raise ValueError(f"Unknown energy_unit {energy_unit!r}. Valid choices: ('Ry', 'eV')")
    if spin is not None and spin not in ("up", "down"):
        raise ValueError(f"Unknown spin {spin!r}. Valid choices: ('up', 'down')")
    if orbitals is None:
        orbitals = ["total"]
    valid_orbitals = ("s", "p", "d", "f", "total")
    invalid_orbitals = [orb for orb in orbitals if orb not in valid_orbitals]
    if invalid_orbitals:
        raise ValueError(f"Unknown orbital(s) {invalid_orbitals!r}. Valid choices: {valid_orbitals}")

    with plt.rc_context(STYLE_RC):
        fig, ax = plt.subplots(figsize=figsize)
        comps_to_plot = [
            c
            for c in result.dos_components
            if (components is None or c.component_index in components) and (spin is None or c.spin == spin)
        ]
        component_channels = {c.spin for c in comps_to_plot}

        unique_pairs = list(
            dict.fromkeys(
                (c.component_index, orb) for c in comps_to_plot for orb in orbitals if getattr(c, orb, None) is not None
            )
        )
        color_map = {pair: COLORS[i % len(COLORS)] for i, pair in enumerate(unique_pairs)}
        legend_labels: dict[tuple[str, str], str] = {
            (c.label, orb): f"{c.label} - {'Total' if orb == 'total' else orb}"
            for c in comps_to_plot
            for orb in orbitals
            if getattr(c, orb, None) is not None
        }

        total_curves: list[tuple[np.ndarray, np.ndarray, str]] = []
        if system_total:
            for channel, curve in (("up", result.total_up), ("down", result.total_down)):
                if spin is not None and channel != spin:
                    continue
                if curve is not None:
                    total_curves.append((curve.energy - ef, curve.values, channel))

        total_channels = {channel for _, _, channel in total_curves}
        has_both_spins = spin is None and component_channels.union(total_channels) == {"up", "down"}

        for comp in comps_to_plot:
            energy = _convert_energy(comp.energy - ef, energy_unit)

            sign = -1 if (has_both_spins and comp.spin == "down") else 1

            for orb in orbitals:
                dos_arr = getattr(comp, orb, None)
                if dos_arr is None:
                    continue
                color = color_map[(comp.component_index, orb)]
                y = sign * _convert_dos(dos_arr, energy_unit)
                label = legend_labels.pop((comp.label, orb), "_nolegend_")
                ax.plot(energy, y, color=color, label=label)
                ax.fill_between(energy, y, alpha=0.12, color=color)

        for i, (energy, values, channel) in enumerate(total_curves):
            sign = -1 if (has_both_spins and channel == "down") else 1
            x = _convert_energy(energy, energy_unit)
            y = sign * _convert_dos(values, energy_unit)
            ax.plot(x, y, color=EF_COLOR, lw=1.0, label="Total" if i == 0 else "_nolegend_")

        if has_both_spins:
            ax.axhline(0, color=ZERO_LINE_COLOR, lw=0.8)
        ax.axvline(0, color=EF_COLOR, lw=0.8, ls="--")
        ax.margins(y=0.03)
        ax.set_xlabel(rf"$E - E_{{\mathrm{{F}}}}$ ({energy_unit})")
        ax.set_ylabel(f"DOS (states/{energy_unit}/cell)")
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend()
        fig.tight_layout()
    return fig


def plot_convergence(
    result: GOResult,
    *,
    field: str = "rms_error",
    figsize: tuple[float, float] = (3.4, 2.6),
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
    valid_fields = ("rms_error", "moment", "total_energy")
    if field not in valid_fields:
        raise ValueError(f"Unknown field {field!r}. Valid choices: {valid_fields}")
    iters = result.iterations

    with plt.rc_context(STYLE_RC):
        if not iters:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "No iteration data", ha="center", va="center")
            return fig

        x = [it.iteration for it in iters]
        y = [getattr(it, field) for it in iters]

        labels = {
            "rms_error": "log$_{10}$RMS Error",
            "moment": "Total moment ($\\mu_B$)",
            "total_energy": "Total energy (Ry)",
        }

        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(x, y, ".-", color=COLORS[1])
        ax.set_xlabel("Iteration")
        ax.set_ylabel(labels.get(field, field))
        ax.set_xlim(left=0)
        ax.yaxis.set_major_formatter(_scientific_mathtext_formatter())
        if result.converged:
            ax.axvline(x[-1], color=COLORS[2], ls="--", lw=0.8)
        fig.tight_layout()
    return fig
