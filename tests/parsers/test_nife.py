"""Tests for the AkaiKKR sample NiFe CPA alloy output file."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from akaitools import parse_go

if TYPE_CHECKING:
    from pathlib import Path

    from akaitools.models import GOResult


class TestNiFeGO:
    """Regression tests for the AkaiKKR sample NiFe CPA GO output."""

    @pytest.fixture(autouse=True)
    def result(self, nife_go: Path) -> None:
        """Parse the NiFe GO fixture for each test."""
        self.r: GOResult = parse_go(nife_go)

    def test_lattice(self) -> None:
        """Check FCC lattice parameters."""
        assert self.r.lattice.bravais == "fcc"
        assert self.r.lattice.a == pytest.approx(6.55, rel=1e-4)

    def test_input_params(self) -> None:
        """Check CPA alloy has ncmpx=2."""
        p = self.r.input_params
        assert p.ntyp == 1
        assert p.natm == 1
        assert p.ncmpx == 2

    def test_convergence(self) -> None:
        """Check that the calculation converged."""
        assert self.r.converged is True
        assert len(self.r.iterations) == 68

    def test_cpa_site_components(self) -> None:
        """Check that the mixed site has two CPA components."""
        assert len(self.r.atom_types) == 1
        site = self.r.atom_types[0]
        assert site.name == "NiFe"
        assert len(site.components) == 2
        atomic_numbers = {int(c.anclr) for c in site.components}
        assert atomic_numbers == {28, 26}  # Ni and Fe

    def test_cpa_concentrations(self) -> None:
        """Check that the CPA concentrations sum to 1."""
        site = self.r.atom_types[0]
        total_conc = sum(c.conc for c in site.components)
        assert total_conc == pytest.approx(1.0, rel=1e-4)

    def test_atomic_properties_per_component(self) -> None:
        """Check that one property block exists per CPA component."""
        assert len(self.r.atomic_properties) == 2

    def test_spin_moments(self) -> None:
        """Check per-component spin moments."""
        props = {p.element: p for p in self.r.atomic_properties}
        assert props["Ni"].spin_moment == pytest.approx(0.69601, rel=1e-3)
        assert props["Fe"].spin_moment == pytest.approx(2.3473, rel=1e-3)
