"""Tests for the AkaiKKR sample GaAs (non-magnetic compound) output file."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from akaitools import parse_go

if TYPE_CHECKING:
    from pathlib import Path

    from akaitools.models import GOResult


class TestGaAsGO:
    """Regression tests for the AkaiKKR sample GaAs non-magnetic GO output."""

    @pytest.fixture(autouse=True)
    def result(self, gaas_go: Path) -> None:
        """Parse the GaAs GO fixture for each test."""
        self.r: GOResult = parse_go(gaas_go)

    def test_lattice(self) -> None:
        """Check FCC lattice parameters."""
        assert self.r.lattice.bravais == "fcc"
        assert self.r.lattice.a == pytest.approx(10.684, rel=1e-4)

    def test_input_params(self) -> None:
        """Check compound has 4 types and 4 atoms."""
        p = self.r.input_params
        assert p.ntyp == 4
        assert p.natm == 4
        assert p.ncmpx == 4

    def test_convergence(self) -> None:
        """Check that the calculation converged."""
        assert self.r.converged is True
        assert len(self.r.iterations) == 57

    def test_non_magnetic(self) -> None:
        """Check that total spin moment is zero (non-magnetic)."""
        last = self.r.iterations[-1]
        assert abs(last.moment) < 1e-4

    def test_atomic_properties_count(self) -> None:
        """Check that property blocks were parsed for all 4 types."""
        assert len(self.r.atomic_properties) == 4

    def test_all_spin_moments_zero(self) -> None:
        """Check that all site spin moments are zero for GaAs."""
        for prop in self.r.atomic_properties:
            assert abs(prop.spin_moment) < 1e-4, f"Expected zero spin moment for {prop.element}, got {prop.spin_moment}"

    def test_element_types(self) -> None:
        """Check that the expected element types are present."""
        type_names = {p.type_name for p in self.r.atomic_properties}
        assert "Ga" in type_names
        assert "As" in type_names

    def test_core_configs_parsed(self) -> None:
        """Check that core configurations were parsed for each type."""
        assert len(self.r.core_configs) == 4
        atomic_numbers = {cfg.z for cfg in self.r.core_configs}
        assert 31 in atomic_numbers  # Ga
        assert 33 in atomic_numbers  # As
