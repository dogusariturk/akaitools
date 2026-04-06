"""Tests for the AkaiKKR sample Li BCC (non-magnetic) DOS output file."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from akaitools import parse_dos
from akaitools.models import DOSCurve, DOSResult

if TYPE_CHECKING:
    from pathlib import Path


class TestLiDOS:
    """Integration tests for the Li BCC non-magnetic DOS file."""

    @pytest.fixture(autouse=True)
    def result(self, li_dos: Path) -> None:
        """Parse the Li DOS fixture for each test."""
        self.r: DOSResult = parse_dos(li_dos)

    def test_ncmpx(self) -> None:
        """Input params reflect a single-component Li calculation."""
        assert self.r.input_params.ncmpx == 1

    def test_one_component(self) -> None:
        """Non-magnetic calculation yields a single DOS component (no spin split)."""
        assert len(self.r.dos_components) == 1

    def test_single_spin_channel(self) -> None:
        """Only the up spin channel is present for a non-magnetic DOS output."""
        spins = {c.spin for c in self.r.dos_components}
        assert spins == {"up"}

    def test_component_element_li(self) -> None:
        """The component's element property is 'Li'."""
        assert self.r.dos_components[0].element == "Li"

    def test_f_orbital_absent(self) -> None:
        """The f-orbital channel is None for Li (lmxtyp=2)."""
        assert self.r.dos_components[0].f is None

    def test_total_up_parsed(self) -> None:
        """Total DOS curve is present and labelled as spin-up."""
        assert self.r.total_up is not None
        assert isinstance(self.r.total_up, DOSCurve)
        assert self.r.total_up.spin == "up"

    def test_total_down_absent(self) -> None:
        """No second total DOS block exists for a non-magnetic calculation."""
        assert self.r.total_down is None

    def test_integrated_up_present(self) -> None:
        """Integrated DOS curve is present."""
        assert self.r.integrated_up is not None

    def test_integrated_down_absent(self) -> None:
        """No second integrated DOS block exists for a non-magnetic calculation."""
        assert self.r.integrated_down is None

    def test_energy_array_nonempty(self) -> None:
        """The energy axis is a non-empty array."""
        comp = self.r.dos_components[0]
        assert isinstance(comp.energy, np.ndarray)
        assert len(comp.energy) > 0
