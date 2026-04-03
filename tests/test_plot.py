"""Tests for akaitools.plot."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl
import matplotlib.figure
import pytest

mpl.use("Agg")

from akaitools import parse_dos, parse_go
from akaitools.plot import plot_convergence, plot_dos, plot_dos_spin

if TYPE_CHECKING:
    from pathlib import Path


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

    def test_no_iterations_returns_figure(self, fe_go: Path) -> None:
        """plot_convergence() handles an empty iterations list gracefully."""
        r = parse_go(fe_go)
        r.iterations = []
        fig = plot_convergence(r)
        assert isinstance(fig, mpl.figure.Figure)


class TestPlotDOS:
    """Tests for plot_dos()."""

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


class TestPlotDOSSpin:
    """Tests for plot_dos_spin()."""

    def test_returns_figure_total(self, fe_dos: Path) -> None:
        """plot_dos_spin() with component=None plots total spin DOS."""
        r = parse_dos(fe_dos)
        fig = plot_dos_spin(r)
        assert isinstance(fig, mpl.figure.Figure)

    def test_total_with_ev(self, fe_dos: Path) -> None:
        """plot_dos_spin() with energy_unit='eV' works for total DOS."""
        r = parse_dos(fe_dos)
        fig = plot_dos_spin(r, energy_unit="eV")
        assert fig is not None

    def test_single_component(self, fe_dos: Path) -> None:
        """plot_dos_spin() with a single component index."""
        r = parse_dos(fe_dos)
        fig = plot_dos_spin(r, component=1)
        assert isinstance(fig, mpl.figure.Figure)

    def test_multiple_components(self, nife_dos: Path) -> None:
        """plot_dos_spin() with a list of component indices."""
        r = parse_dos(nife_dos)
        fig = plot_dos_spin(r, component=[1, 2])
        assert isinstance(fig, mpl.figure.Figure)

    def test_orbital_d(self, fe_dos: Path) -> None:
        """plot_dos_spin() accepts orbital='d'."""
        r = parse_dos(fe_dos)
        fig = plot_dos_spin(r, component=1, orbital="d")
        assert fig is not None

    def test_invalid_orbital_raises(self, fe_dos: Path) -> None:
        """plot_dos_spin() raises ValueError for an invalid orbital name."""
        r = parse_dos(fe_dos)
        with pytest.raises(ValueError, match="Unknown orbital"):
            plot_dos_spin(r, component=1, orbital="xyz")

    def test_no_total_curves(self, fe_dos: Path) -> None:
        """plot_dos_spin() with component=None handles missing total curves."""
        r = parse_dos(fe_dos)
        r.total_up = None
        r.total_down = None
        fig = plot_dos_spin(r)
        assert isinstance(fig, mpl.figure.Figure)
