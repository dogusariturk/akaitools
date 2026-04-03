"""Tests for the AkaiKKR sample Fe BCC output file."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from akaitools import parse_go
from akaitools.models import ChargeDensityAtNucleus, HyperfineField

if TYPE_CHECKING:
    from pathlib import Path

    from akaitools.models import GOResult


class TestFeGO:
    """Regression tests for the AkaiKKR sample Fe BCC GO output."""

    @pytest.fixture(autouse=True)
    def result(self, fe_go: Path) -> None:
        """Parse the Fe GO fixture for each test."""
        self.r: GOResult = parse_go(fe_go)

    def test_mesh_params(self) -> None:
        """Check header mesh parameters."""
        assert self.r.meshr == 400
        assert self.r.mse == 35
        assert self.r.ng == 21
        assert self.r.mxl == 3

    def test_lattice(self) -> None:
        """Check BCC lattice parameters."""
        assert self.r.lattice.bravais == "bcc"
        assert self.r.lattice.a == pytest.approx(5.27, rel=1e-4)

    def test_input_params(self) -> None:
        """Check parsed input parameters."""
        p = self.r.input_params
        assert p.ntyp == 1
        assert p.natm == 1
        assert p.ncmpx == 1
        assert p.magtyp == "mag"

    def test_convergence(self) -> None:
        """Check that the calculation converged."""
        assert self.r.converged is True
        assert len(self.r.iterations) == 38

    def test_final_moment(self) -> None:
        """Check the final magnetic moment."""
        last = self.r.iterations[-1]
        assert last.moment == pytest.approx(2.1686, rel=1e-3)

    def test_atom_type(self) -> None:
        """Check the single Fe atom type."""
        assert len(self.r.atom_types) == 1
        site = self.r.atom_types[0]
        assert site.name == "Fe"
        # Pure element: one component with Z=26 at full concentration
        assert len(site.components) == 1
        assert int(site.components[0].anclr) == 26
        assert site.components[0].conc == pytest.approx(1.0)

    def test_atomic_properties_count(self) -> None:
        """Check that one property block was parsed."""
        assert len(self.r.atomic_properties) == 1

    def test_spin_moment(self) -> None:
        """Check the Fe spin magnetic moment."""
        p = self.r.atomic_properties[0]
        assert p.element == "Fe"
        assert p.spin_moment == pytest.approx(2.16862, rel=1e-4)

    def test_hyperfine_field_present(self) -> None:
        """Check that hyperfine field is parsed and not None."""
        p = self.r.atomic_properties[0]
        assert isinstance(p.hyperfine_field, HyperfineField)

    def test_hyperfine_field_values(self) -> None:
        """Check the Fe hyperfine field components."""
        hf = self.r.atomic_properties[0].hyperfine_field
        assert hf is not None
        assert hf.total == pytest.approx(-259.216, rel=1e-4)
        assert hf.core == pytest.approx(-221.111, rel=1e-4)
        assert hf.valence == pytest.approx(-38.105, rel=1e-4)

    def test_hyperfine_core_contributions(self) -> None:
        """Check that core-shell contributions were parsed."""
        hf = self.r.atomic_properties[0].hyperfine_field
        assert hf is not None
        assert "1s" in hf.core_contributions
        assert "2s" in hf.core_contributions
        assert "3s" in hf.core_contributions
        assert hf.core_contributions["1s"] == pytest.approx(-18.528, rel=1e-3)

    def test_charge_density_at_nucleus(self) -> None:
        """Check the Fe charge density at the nucleus."""
        cd = self.r.atomic_properties[0].charge_density_at_nucleus
        assert isinstance(cd, ChargeDensityAtNucleus)
        assert cd.total == pytest.approx(11820.5093, rel=1e-4)
        assert cd.core == pytest.approx(11814.6068, rel=1e-4)
        assert cd.valence == pytest.approx(5.9025, rel=1e-3)

    def test_core_config(self) -> None:
        """Check the Fe core configuration (Z=26)."""
        assert len(self.r.core_configs) == 1
        cfg = self.r.core_configs[0]
        assert cfg.z == 26
        assert len(cfg.up) == len(cfg.down)
        assert len(cfg.up) > 0

    def test_system_info(self) -> None:
        """Check that system info was parsed."""
        si = self.r.system_info
        assert si.os != ""
        assert si.num_cores > 0
        assert si.elapsed_time > 0.0
