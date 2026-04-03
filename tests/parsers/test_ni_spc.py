"""Tests for the AkaiKKR sample Ni FCC SPC output file."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from akaitools import parse_spc

if TYPE_CHECKING:
    from akaitools.models import SPCResult

SAMPLES = Path(__file__).parent.parent / "data"


class TestNiSPC:
    """Regression tests for the AkaiKKR sample Ni FCC SPC log."""

    @pytest.fixture(autouse=True)
    def result(self, ni_spc: Path) -> None:
        """Parse the Ni SPC fixture without spectral data."""
        self.r: SPCResult = parse_spc(ni_spc)

    def test_go_is_spc(self) -> None:
        """Input params reflect an SPC calculation."""
        assert self.r.input_params.go == "spc"

    def test_lattice_fcc(self) -> None:
        """Lattice is FCC with the correct lattice constant."""
        assert self.r.lattice.bravais == "fcc"
        assert self.r.lattice.a == pytest.approx(6.66, rel=1e-4)

    def test_atom_type_ni(self) -> None:
        """One atom type (Ni) is parsed."""
        assert len(self.r.atom_types) == 1
        assert self.r.atom_types[0].name == "Ni"

    def test_core_config_z28(self) -> None:
        """Core configuration for Z=28 is present."""
        assert len(self.r.core_configs) == 1
        assert self.r.core_configs[0].z == 28

    def test_iteration_parsed(self) -> None:
        """The single SCF iteration block is parsed correctly."""
        assert self.r.iteration is not None
        assert self.r.iteration.iteration == 1

    def test_no_spectral_data_by_default(self) -> None:
        """Without base_dir or explicit paths, spectral data is not found."""
        assert self.r.spectral_up is None
        assert self.r.spectral_down is None


class TestNiSPCWithData:
    """Ni SPC with spectral data loaded via base_dir."""

    @pytest.fixture(autouse=True)
    def result(self, ni_spc: Path) -> None:
        """Parse the Ni SPC fixture with spectral data via base_dir."""
        self.r: SPCResult = parse_spc(ni_spc, base_dir=SAMPLES)

    def test_spectral_up_loaded(self) -> None:
        """Spectral up data is loaded when base_dir is provided."""
        assert self.r.spectral_up is not None

    def test_spectral_up_shape(self) -> None:
        """Ni has 300 k-points and 6 high-symmetry labels."""
        assert self.r.spectral_up is not None
        assert self.r.spectral_up.data is not None
        assert self.r.spectral_up.data.shape == (200, 300)
        assert self.r.spectral_up.kmesh.n_sym_points == 6

    def test_spectral_down_loaded(self) -> None:
        """Spectral down data is loaded with a non-None data matrix."""
        assert self.r.spectral_down is not None
        assert self.r.spectral_down.data is not None
