"""Tests for the AkaiKKR sample Li BCC (non-magnetic) output file."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from akaitools import parse_go
from akaitools.models import ChargeDensityAtNucleus, HyperfineField

if TYPE_CHECKING:
    from pathlib import Path

    from akaitools.models import GOResult


class TestLiGO:
    """Regression tests for the AkaiKKR sample Li BCC non-magnetic GO output."""

    @pytest.fixture(autouse=True)
    def result(self, li_go: Path) -> None:
        """Parse the Li GO fixture for each test."""
        self.r: GOResult = parse_go(li_go)

    def test_mesh_params(self) -> None:
        """Check header mesh parameters."""
        assert self.r.meshr == 400
        assert self.r.mse == 43
        assert self.r.ng == 21
        assert self.r.mxl == 3

    def test_lattice(self) -> None:
        """Check BCC lattice parameters."""
        assert self.r.lattice.bravais == "bcc"
        assert self.r.lattice.a == pytest.approx(6.633, rel=1e-4)

    def test_input_params(self) -> None:
        """Check parsed input parameters."""
        p = self.r.input_params
        assert p.ntyp == 1
        assert p.natm == 1
        assert p.ncmpx == 1
        assert p.magtyp == "nmag"

    def test_convergence(self) -> None:
        """Check that the calculation converged."""
        assert self.r.converged is True
        assert len(self.r.iterations) == 53

    def test_final_moment_zero(self) -> None:
        """Check the final magnetic moment is zero (non-magnetic)."""
        last = self.r.iterations[-1]
        assert abs(last.moment) < 1e-4

    def test_atom_type(self) -> None:
        """Check the single Li atom type."""
        assert len(self.r.atom_types) == 1
        site = self.r.atom_types[0]
        assert site.name == "Li"
        assert len(site.components) == 1
        assert int(site.components[0].anclr) == 3
        assert site.components[0].conc == pytest.approx(1.0)

    def test_atomic_properties_count(self) -> None:
        """Check that one property block was parsed."""
        assert len(self.r.atomic_properties) == 1

    def test_spin_moment_zero(self) -> None:
        """Check the Li spin magnetic moment is zero."""
        p = self.r.atomic_properties[0]
        assert p.element == "Li"
        assert abs(p.spin_moment) < 1e-4

    def test_hyperfine_field_present(self) -> None:
        """Check that hyperfine field is parsed and not None."""
        p = self.r.atomic_properties[0]
        assert isinstance(p.hyperfine_field, HyperfineField)

    def test_hyperfine_field_values(self) -> None:
        """Check the Li hyperfine field is effectively zero."""
        hf = self.r.atomic_properties[0].hyperfine_field
        assert hf is not None
        assert abs(hf.total) < 1e-2
        assert abs(hf.core) < 1e-2
        assert abs(hf.valence) < 1e-2

    def test_charge_density_at_nucleus(self) -> None:
        """Check the Li charge density at the nucleus."""
        cd = self.r.atomic_properties[0].charge_density_at_nucleus
        assert isinstance(cd, ChargeDensityAtNucleus)
        assert cd.total == pytest.approx(13.5724, rel=1e-4)
        assert cd.core == pytest.approx(13.3531, rel=1e-4)
        assert cd.valence == pytest.approx(0.2193, rel=1e-3)

    def test_core_config(self) -> None:
        """Check the Li core configuration (Z=3)."""
        assert len(self.r.core_configs) == 1
        cfg = self.r.core_configs[0]
        assert cfg.z == 3

    def test_system_info(self) -> None:
        """Check that system info was parsed."""
        si = self.r.system_info
        assert si.os != ""
        assert si.num_cores > 0
        assert si.elapsed_time > 0.0
