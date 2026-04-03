"""Tests for the AkaiKKR sample Ni FCC output file."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from akaitools import parse_go
from akaitools.models import HyperfineField

if TYPE_CHECKING:
    from pathlib import Path

    from akaitools.models import GOResult


class TestNiGO:
    """Regression tests for the AkaiKKR sample Ni FCC GO output."""

    @pytest.fixture(autouse=True)
    def result(self, ni_go: Path) -> None:
        """Parse the Ni GO fixture for each test."""
        self.r: GOResult = parse_go(ni_go)

    def test_mesh_params(self) -> None:
        """Check header mesh parameters."""
        assert self.r.meshr == 400
        assert self.r.mse == 35
        assert self.r.mxl == 3

    def test_lattice(self) -> None:
        """Check FCC lattice parameters."""
        assert self.r.lattice.bravais == "fcc"
        assert self.r.lattice.a == pytest.approx(6.66, rel=1e-4)

    def test_input_params(self) -> None:
        """Check parsed input parameters."""
        p = self.r.input_params
        assert p.ntyp == 1
        assert p.natm == 1
        assert p.ncmpx == 1

    def test_convergence(self) -> None:
        """Check that the calculation converged."""
        assert self.r.converged is True
        assert len(self.r.iterations) == 52

    def test_spin_moment(self) -> None:
        """Check the Ni spin magnetic moment (weak ferromagnet)."""
        p = self.r.atomic_properties[0]
        assert p.element == "Ni"
        assert p.spin_moment == pytest.approx(0.57827, rel=1e-3)

    def test_hyperfine_field(self) -> None:
        """Check that the Ni hyperfine field is parsed and not None."""
        p = self.r.atomic_properties[0]
        assert isinstance(p.hyperfine_field, HyperfineField)
        assert p.hyperfine_field.total == pytest.approx(-89.781, rel=1e-3)

    def test_core_config(self) -> None:
        """Check the Ni core configuration (Z=28)."""
        assert len(self.r.core_configs) == 1
        assert self.r.core_configs[0].z == 28
