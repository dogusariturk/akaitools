"""Tests for the AkaiKKR sample NiFe CPA alloy SPC output file."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest

from akaitools import parse_spc

if TYPE_CHECKING:
    from akaitools.models import SPCResult

SAMPLES = Path(__file__).parent.parent / "data"


class TestNiFeSPC:
    """Regression tests for the AkaiKKR sample NiFe CPA SPC log."""

    @pytest.fixture(autouse=True)
    def result(self, nife_spc: Path) -> None:
        """Parse the NiFe SPC fixture without spectral data."""
        self.r: SPCResult = parse_spc(nife_spc)

    def test_go_is_spc(self) -> None:
        """Input params reflect an SPC calculation."""
        assert self.r.input_params.go == "spc"

    def test_lattice_fcc(self) -> None:
        """Lattice is FCC."""
        assert self.r.lattice.bravais == "fcc"

    def test_cpa_alloy(self) -> None:
        """NiFe has one CPA site with two components."""
        assert len(self.r.atom_types) == 1
        assert len(self.r.atom_types[0].components) == 2

    def test_iteration_parsed(self) -> None:
        """The single SCF iteration block is parsed correctly."""
        assert self.r.iteration is not None
        assert self.r.iteration.iteration == 1


class TestNiFeSPCWithData:
    """NiFe SPC with populated spectral function data (300 k-points, 6 labels)."""

    @pytest.fixture(autouse=True)
    def result(self, nife_spc: Path) -> None:
        """Parse the NiFe SPC fixture with spectral data via base_dir."""
        self.r: SPCResult = parse_spc(nife_spc, base_dir=SAMPLES)

    def test_spectral_up_populated(self) -> None:
        """Spectral up data is loaded and has a non-None data matrix."""
        sf = self.r.spectral_up
        assert sf is not None
        assert sf.data is not None

    def test_spectral_up_shape(self) -> None:
        """NiFe spectral up matrix has shape (200, 300)."""
        assert self.r.spectral_up is not None
        data = self.r.spectral_up.data
        assert data is not None
        assert data.shape == (200, 300)

    def test_spectral_up_n_sym_points(self) -> None:
        """NiFe spectral up k-mesh has 6 high-symmetry points."""
        assert self.r.spectral_up is not None
        assert self.r.spectral_up.kmesh.n_sym_points == 6

    def test_spectral_up_gamma_label(self) -> None:
        """Gamma point label is at index 138."""
        assert self.r.spectral_up is not None
        hs = self.r.spectral_up.kmesh.high_symmetry_indices
        assert 138 in hs
        assert hs[138] == "(0 0 0)"

    def test_spectral_up_all_labels(self) -> None:
        """All six high-symmetry labels match the fixture."""
        assert self.r.spectral_up is not None
        hs = self.r.spectral_up.kmesh.high_symmetry_indices
        assert len(hs) == 6
        assert hs[1] == "(1 1/2 0)"
        assert hs[63] == "(1/2 1/2 1/2)"
        assert hs[226] == "(1 0 0)"
        assert hs[269] == "(1 1/2 0)"
        assert hs[300] == "(3/4 3/4 0)"

    def test_spectral_up_data_non_negative(self) -> None:
        """BSF intensities must be non-negative."""
        assert self.r.spectral_up is not None
        assert self.r.spectral_up.data is not None
        assert np.all(self.r.spectral_up.data >= 0.0)

    def test_spectral_down_populated(self) -> None:
        """Spectral down data is loaded and has shape (200, 300)."""
        assert self.r.spectral_down is not None
        assert self.r.spectral_down.data is not None
        assert self.r.spectral_down.data.shape == (200, 300)

    def test_explicit_override_gives_same_result(self, nife_spc: Path) -> None:
        """Passing data_up explicitly should yield the same data as auto-discovery."""
        r2 = parse_spc(nife_spc, data_up=SAMPLES / "data" / "nife_up.spc")
        assert r2.spectral_up is not None
        assert r2.spectral_up.data is not None
        assert self.r.spectral_up is not None
        np.testing.assert_array_equal(r2.spectral_up.data, self.r.spectral_up.data)
