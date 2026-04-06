"""Tests for the AkaiKKR sample Li BCC (non-magnetic) SPC output file."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest

from akaitools import parse_spc

if TYPE_CHECKING:
    from akaitools.models import SPCResult

SAMPLES = Path(__file__).parent.parent / "data"


class TestLiSPC:
    """Regression tests for the AkaiKKR sample Li BCC SPC log (no spectral data)."""

    @pytest.fixture(autouse=True)
    def result(self, li_spc: Path) -> None:
        """Parse the Li SPC fixture without spectral data."""
        self.r: SPCResult = parse_spc(li_spc)

    def test_go_is_spc(self) -> None:
        """Input params reflect an SPC calculation."""
        assert self.r.input_params.go == "spc"

    def test_mesh_params(self) -> None:
        """Mesh parameters match the Li BCC fixture values."""
        assert self.r.meshr == 400
        assert self.r.mse == 201
        assert self.r.ng == 21
        assert self.r.mxl == 3

    def test_lattice(self) -> None:
        """Lattice is BCC with the correct lattice constant."""
        assert self.r.lattice.bravais == "bcc"
        assert self.r.lattice.a == pytest.approx(6.633, rel=1e-4)

    def test_spc_params_ew_ez(self) -> None:
        """Energy window and zero energy match the Li fixture."""
        assert self.r.spc_params.ew == pytest.approx(0.41610, rel=1e-4)
        assert self.r.spc_params.ez == pytest.approx(0.80000, rel=1e-4)

    def test_spc_params_eta(self) -> None:
        """Pre-broadening and broadening parameters match the Li fixture."""
        assert self.r.spc_params.preta == pytest.approx(0.35542, rel=1e-4)
        assert self.r.spc_params.eta == pytest.approx(0.35542, rel=1e-4)

    def test_spc_params_mesh(self) -> None:
        """SPC mesh parameters match the Li fixture."""
        assert self.r.spc_params.last == 243
        assert self.r.spc_params.np == 19
        assert self.r.spc_params.ngpt == 273
        assert self.r.spc_params.nrpt == 169
        assert self.r.spc_params.nk == 1961
        assert self.r.spc_params.nd == 1

    def test_spc_params_symop(self) -> None:
        """Symmetry operation labels are parsed and include the identity."""
        assert len(self.r.spc_params.symop_labels) > 0
        assert "E" in self.r.spc_params.symop_labels

    def test_single_iteration_parsed(self) -> None:
        """The single SCF iteration block is parsed correctly."""
        assert self.r.iteration is not None
        assert self.r.iteration.iteration == 1
        assert self.r.iteration.neu == pytest.approx(3.9451, rel=1e-3)
        assert abs(self.r.iteration.moment) < 1e-4

    def test_atom_type(self) -> None:
        """One atom type (Li) is parsed."""
        assert len(self.r.atom_types) == 1
        assert self.r.atom_types[0].name == "Li"

    def test_core_config(self) -> None:
        """Core configuration for Z=3 is present."""
        assert len(self.r.core_configs) == 1
        assert self.r.core_configs[0].z == 3

    def test_atomic_properties(self) -> None:
        """Atomic properties for Li are parsed and moment is zero."""
        assert len(self.r.atomic_properties) == 1
        assert self.r.atomic_properties[0].element == "Li"
        assert abs(self.r.atomic_properties[0].spin_moment) < 1e-4

    def test_no_spectral_data_by_default(self) -> None:
        """Without base_dir or explicit paths, spectral data is not found."""
        assert self.r.spectral_up is None
        assert self.r.spectral_down is None


class TestLiSPCWithData:
    """Li SPC with spin-up spectral data loaded via explicit path.

    li_dn.spc is 0 bytes (expected for a non-magnetic calculation), so only
    the up channel is loaded.
    """

    @pytest.fixture(autouse=True)
    def result(self, li_spc: Path) -> None:
        """Parse the Li SPC fixture with explicit spin-up data path."""
        self.r: SPCResult = parse_spc(li_spc, data_up=SAMPLES / "data" / "li_up.spc")

    def test_spectral_up_loaded(self) -> None:
        """Spectral up data is loaded when data_up is provided."""
        assert self.r.spectral_up is not None

    def test_spectral_up_populated(self) -> None:
        """Li up.spc contains a populated BSF matrix."""
        assert self.r.spectral_up is not None
        assert self.r.spectral_up.data is not None
        assert self.r.spectral_up.data.shape == (200, 300)
        assert self.r.spectral_up.spin == "up"
        assert np.all(self.r.spectral_up.data >= 0.0)

    def test_spectral_up_kmesh(self) -> None:
        """k-mesh metadata for the Li up channel is parsed correctly."""
        assert self.r.spectral_up is not None
        km = self.r.spectral_up.kmesh
        assert km.n_energy == 200
        assert km.n_sym_points == 6
        assert km.energy_min == pytest.approx(-0.5970, rel=1e-4)
        assert km.energy_max == pytest.approx(0.5970, rel=1e-4)
        assert km.high_symmetry_indices == {
            1: "(0 0 0)",
            80: "(0 1 0)",
            136: "(1/2 1/2 0)",
            176: "(1/2 1/2 1/2)",
            244: "(0 0 0)",
            300: "(1/2 1/2 0)",
        }

    def test_spectral_down_none(self) -> None:
        """Spectral down is None — li_dn.spc is empty and no path was provided."""
        assert self.r.spectral_down is None
