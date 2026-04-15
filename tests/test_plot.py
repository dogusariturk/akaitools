"""Tests for akaitools.plot."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl
import matplotlib.axes
import matplotlib.figure
import matplotlib.lines
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.ticker import ScalarFormatter

mpl.use("Agg")

from akaitools import parse_dos, parse_go
from akaitools.errors import InvalidParameterError
from akaitools.plot import plot_convergence, plot_dos
from akaitools.utils import RY_TO_EV

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(autouse=True)
def close_figures() -> None:
    """Close Matplotlib figures after each test."""
    plt.close("all")


class TestPlotConvergence:
    """Tests for plot_convergence()."""

    def test_returns_figure(self, fe_go: Path) -> None:
        """plot_convergence() returns a Matplotlib Figure."""
        r = parse_go(fe_go)
        fig = plot_convergence(r)
        assert isinstance(fig, mpl.figure.Figure)

    def test_field_moment(self, fe_go: Path) -> None:
        """plot_convergence() accepts field='moment'."""
        r = parse_go(fe_go)
        fig = plot_convergence(r, field="moment")
        assert fig is not None

    def test_field_total_energy(self, fe_go: Path) -> None:
        """plot_convergence() accepts field='total_energy'."""
        r = parse_go(fe_go)
        fig = plot_convergence(r, field="total_energy")
        assert fig is not None

    def test_field_neu(self, fe_go: Path) -> None:
        """plot_convergence() accepts field='neu'."""
        r = parse_go(fe_go)
        fig = plot_convergence(r, field="neu")
        assert fig is not None

    def test_iteration_axis_starts_at_zero(self, fe_go: Path) -> None:
        """plot_convergence() anchors the iteration axis at zero."""
        r = parse_go(fe_go)
        fig = plot_convergence(r)
        ax = fig.axes[0]
        assert ax.get_xlim()[0] == pytest.approx(0.0)

    def test_total_energy_uses_mathtext_without_offset(self, fe_go: Path) -> None:
        """plot_convergence() disables additive axis offsets."""
        r = parse_go(fe_go)
        fig = plot_convergence(r, field="total_energy")
        ax = fig.axes[0]
        formatter = ax.yaxis.get_major_formatter()

        fig.canvas.draw()

        assert isinstance(formatter, ScalarFormatter)
        assert formatter.get_useOffset() is False
        assert ax.yaxis.get_offset_text().get_text() == ""

    def test_no_iterations_returns_figure(self, fe_go: Path) -> None:
        """plot_convergence() handles an empty iterations list gracefully."""
        r = parse_go(fe_go)
        r.iterations = []
        fig = plot_convergence(r)
        assert isinstance(fig, mpl.figure.Figure)

    def test_invalid_field_raises(self, fe_go: Path) -> None:
        """plot_convergence() raises InvalidParameterError for an unknown field."""
        r = parse_go(fe_go)
        with pytest.raises(InvalidParameterError, match="Unknown field"):
            plot_convergence(r, field="unknown")


class TestPlotDOS:
    """Tests for plot_dos()."""

    @staticmethod
    def _curve_lines(ax: mpl.axes.Axes) -> list[mpl.lines.Line2D]:
        """Return plotted DOS curves, excluding reference guide lines."""
        return [
            line
            for line in ax.lines
            if len(set(np.asarray(line.get_xdata()).tolist())) > 1 and len(set(np.asarray(line.get_ydata()).tolist())) > 1
        ]

    def test_returns_figure(self, fe_dos: Path) -> None:
        """plot_dos() returns a Matplotlib Figure."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r)
        assert isinstance(fig, mpl.figure.Figure)

    def test_energy_unit_ev(self, fe_dos: Path) -> None:
        """plot_dos() works with energy_unit='eV'."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r, energy_unit="eV")
        assert fig is not None

    def test_energy_unit_ev_converts_dos_values(self, fe_dos: Path) -> None:
        """plot_dos() rescales DOS from states/Ry to states/eV."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r, components=[1], spin="up", orbitals=["total"], energy_unit="eV")

        ax = fig.axes[0]
        component = next(c for c in r.dos_components if c.component_index == 1 and c.spin == "up")

        assert ax.get_ylabel() == "DOS (states/eV/cell)"
        assert ax.lines[0].get_ydata() == pytest.approx(component.total / RY_TO_EV)

    def test_has_vertical_padding(self, fe_dos: Path) -> None:
        """plot_dos() leaves a small y-margin above and below the curves."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r, components=[1])
        ax = fig.axes[0]
        curves = self._curve_lines(ax)
        ymin = min(float(min(np.asarray(line.get_ydata()).tolist())) for line in curves)
        ymax = max(float(max(np.asarray(line.get_ydata()).tolist())) for line in curves)
        axis_ymin, axis_ymax = ax.get_ylim()

        assert axis_ymin < ymin
        assert axis_ymax > ymax

    def test_legend_merges_spin_channels(self, fe_dos: Path) -> None:
        """plot_dos() uses one legend entry for up/down of the same orbital."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r, components=[1], orbitals=["total"])
        legend = fig.axes[0].get_legend()

        assert legend is not None
        component = r.get_component(1, "up")
        assert component is not None
        assert [text.get_text() for text in legend.get_texts()] == [f"{component.label} - Total", "Total"]

    def test_spin_filtered_legend_omits_spin_name(self, fe_dos: Path) -> None:
        """plot_dos() legend labels do not include spin names."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r, components=[1], spin="up", orbitals=["total"])
        legend = fig.axes[0].get_legend()

        assert legend is not None
        component = r.get_component(1, "up")
        assert component is not None
        assert [text.get_text() for text in legend.get_texts()] == [f"{component.label} - Total", "Total"]

    def test_spin_filter_up(self, fe_dos: Path) -> None:
        """plot_dos() accepts spin='up' filter."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r, spin="up")
        assert fig is not None

    def test_component_filter(self, fe_dos: Path) -> None:
        """plot_dos() accepts components=[1] filter."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r, components=[1])
        assert fig is not None

    def test_orbital_filter_spd(self, fe_dos: Path) -> None:
        """plot_dos() accepts orbitals=['s', 'p', 'd'] filter."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r, orbitals=["s", "p", "d"])
        assert fig is not None

    def test_orbital_missing_skipped(self, fe_dos: Path) -> None:
        """plot_dos() skips f orbital when it's None without raising."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r, orbitals=["f"])
        assert fig is not None

    def test_nife_multiple_components(self, nife_dos: Path) -> None:
        """plot_dos() handles CPA results with multiple components."""
        r = parse_dos(nife_dos)
        fig = plot_dos(r)
        assert isinstance(fig, mpl.figure.Figure)

    def test_system_total_overlay_returns_figure(self, fe_dos: Path) -> None:
        """plot_dos(system_total=True) overlays the system total DOS."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r, system_total=True)
        assert isinstance(fig, mpl.figure.Figure)

    def test_system_total_overlay_with_ev(self, fe_dos: Path) -> None:
        """plot_dos(system_total=True) with energy_unit='eV' rescales total DOS."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r, system_total=True, orbitals=[], energy_unit="eV")
        ax = fig.axes[0]
        total_up = r.total_up

        assert total_up is not None
        assert ax.get_ylabel() == "DOS (states/eV/cell)"
        assert ax.lines[0].get_ydata() == pytest.approx(total_up.values / RY_TO_EV)

    def test_system_total_overlay_uses_distinct_legend_entry(self, fe_dos: Path) -> None:
        """plot_dos(system_total=True) adds a system-total legend entry."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r, components=[1], orbitals=["total"], system_total=True)
        legend = fig.axes[0].get_legend()

        assert legend is not None
        component = r.get_component(1, "up")
        assert component is not None
        assert [text.get_text() for text in legend.get_texts()] == [f"{component.label} - Total", "Total"]

    def test_invalid_orbital_raises(self, fe_dos: Path) -> None:
        """plot_dos() raises InvalidParameterError for an invalid orbital name."""
        r = parse_dos(fe_dos)
        with pytest.raises(InvalidParameterError, match="Unknown orbital"):
            plot_dos(r, components=[1], orbitals=["xyz"])

    def test_invalid_energy_unit_raises(self, fe_dos: Path) -> None:
        """plot_dos() raises InvalidParameterError for an unknown energy unit."""
        r = parse_dos(fe_dos)
        with pytest.raises(InvalidParameterError, match="Unknown energy_unit"):
            plot_dos(r, energy_unit="J")

    def test_invalid_spin_raises(self, fe_dos: Path) -> None:
        """plot_dos() raises InvalidParameterError for an unknown spin value."""
        r = parse_dos(fe_dos)
        with pytest.raises(InvalidParameterError, match="Unknown spin"):
            plot_dos(r, spin="left")

    def test_system_total_only_with_empty_orbitals(self, fe_dos: Path) -> None:
        """plot_dos() can show only the system total by passing orbitals=[]."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r, system_total=True, orbitals=[])
        ax = fig.axes[0]

        assert len(self._curve_lines(ax)) == 2
        assert isinstance(fig, mpl.figure.Figure)

    def test_system_total_handles_single_spin_channel(self, fe_dos: Path) -> None:
        """plot_dos(system_total=True) works when only one spin channel is available."""
        r = parse_dos(fe_dos)
        r.total_down = None
        r.dos_components = [comp for comp in r.dos_components if comp.spin == "up"]
        fig = plot_dos(r, system_total=True, orbitals=[])
        ax = fig.axes[0]

        assert len(self._curve_lines(ax)) == 1
        assert isinstance(fig, mpl.figure.Figure)

    def test_system_total_overlays_component_totals(self, fe_dos: Path) -> None:
        """plot_dos(system_total=True) can show component totals and system total together."""
        r = parse_dos(fe_dos)
        fig = plot_dos(r, components=[1], orbitals=["total"], system_total=True)
        ax = fig.axes[0]

        assert len(self._curve_lines(ax)) == 4
        assert isinstance(fig, mpl.figure.Figure)
