"""Self-consistency convergence plotting for AkaiKKR GO results."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from akaitools.models import GOResult

from akaitools.errors import InvalidParameterError
from akaitools.plotting.common import plt, scientific_mathtext_formatter
from akaitools.plotting.styles import COLORS, STYLE_RC


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
            ``"moment"``, ``"total_energy"``, ``"total_energy_ev"``, or ``"neu"``.
        figsize: Matplotlib figure size ``(width, height)`` in inches.

    Returns:
        The populated Matplotlib figure.
    """
    valid_fields = ("rms_error", "moment", "total_energy", "total_energy_ev", "neu")
    if field not in valid_fields:
        raise InvalidParameterError(f"Unknown field {field!r}. Valid choices: {valid_fields}")
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
            "moment": "Total Moment ($\\mu_B$)",
            "total_energy": "Total Energy (Ry)",
            "total_energy_ev": "Total Energy (eV)",
            "neu": "Charge Neutrality",
        }

        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(
            x,
            y,
            color=COLORS[0],
            lw=1.2,
            marker="o",
            markersize=2.1,
            markevery=max(len(x) // 12, 1),
        )
        ax.set_xlabel("Iteration")
        ax.set_ylabel(labels.get(field, field))
        ax.set_xlim(left=0)
        ax.yaxis.set_major_formatter(scientific_mathtext_formatter())
        if result.converged:
            ax.axvline(x[-1], color=COLORS[2], ls="--", lw=0.8)
        fig.tight_layout()
    return fig
