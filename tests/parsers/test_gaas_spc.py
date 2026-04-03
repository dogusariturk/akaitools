"""Tests for the AkaiKKR sample GaAs SPC output file."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from akaitools import parse_spc

if TYPE_CHECKING:
    from akaitools.models import SPCResult

SAMPLES = Path(__file__).parent.parent / "data"


class TestGaAsSPC:
    """Regression tests for the AkaiKKR sample GaAs SPC log."""

    @pytest.fixture(autouse=True)
    def result(self, gaas_spc: Path) -> None:
        """Parse the GaAs SPC fixture without spectral data."""
        self.r: SPCResult = parse_spc(gaas_spc)

    def test_go_is_spc(self) -> None:
        """Input params reflect an SPC calculation."""
        assert self.r.input_params.go == "spc"

    def test_lattice_fcc(self) -> None:
        """Lattice is FCC."""
        assert self.r.lattice.bravais == "fcc"

    def test_non_magnetic(self) -> None:
        """GaAs is non-magnetic; spin moment should be zero."""
        for ap in self.r.atomic_properties:
            assert ap.spin_moment == pytest.approx(0.0, abs=1e-4)

    def test_multiple_atom_types(self) -> None:
        """GaAs has Ga and As site types."""
        names = {at.name for at in self.r.atom_types}
        assert "Ga" in names
        assert "As" in names

    def test_iteration_parsed(self) -> None:
        """The single SCF iteration block is parsed correctly."""
        assert self.r.iteration is not None
        assert self.r.iteration.iteration == 1

    def test_no_spectral_data_by_default(self) -> None:
        """Without base_dir or explicit paths, spectral data is not found."""
        assert self.r.spectral_up is None
        assert self.r.spectral_down is None


class TestGaAsSPCWithData:
    """GaAs SPC with spectral data loaded via base_dir."""

    @pytest.fixture(autouse=True)
    def result(self, gaas_spc: Path) -> None:
        """Parse the GaAs SPC fixture with spectral data via base_dir."""
        self.r: SPCResult = parse_spc(gaas_spc, base_dir=SAMPLES)

    def test_spectral_up_loaded(self) -> None:
        """Spectral up data is loaded when base_dir is provided."""
        assert self.r.spectral_up is not None

    def test_spectral_up_empty_matrix(self) -> None:
        """GaAs up.spc has n_sym_points=0, so data is None."""
        assert self.r.spectral_up is not None
        assert self.r.spectral_up.data is None
        assert self.r.spectral_up.kmesh.n_sym_points == 0
