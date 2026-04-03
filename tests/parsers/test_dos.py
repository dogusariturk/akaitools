"""Tests for the DOS output file parser."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from akaitools import parse_dos
from akaitools.errors import ParseError
from akaitools.models import DOSCurve, DOSResult
from akaitools.parsers.dos import (
    collect_components,
    parse_curve_block,
    parse_dos_components,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestFeDOS:
    """Integration tests for the Fe BCC DOS file."""

    @pytest.fixture(autouse=True)
    def result(self, fe_dos: Path) -> None:
        """Parse the Fe DOS fixture for each test."""
        self.r: DOSResult = parse_dos(fe_dos)

    def test_returns_dos_result(self) -> None:
        """parse_dos returns a DOSResult instance."""
        assert isinstance(self.r, DOSResult)

    def test_lattice(self) -> None:
        """Parsed lattice matches the Fe BCC structure."""
        assert self.r.lattice.bravais == "bcc"
        assert self.r.lattice.a == pytest.approx(5.27, rel=1e-4)

    def test_input_params(self) -> None:
        """Input params reflect a single-type, single-component calculation."""
        assert self.r.input_params.ntyp == 1
        assert self.r.input_params.ncmpx == 1

    def test_dos_components_count(self) -> None:
        """One component times two spin channels yields two DOS components."""
        assert len(self.r.dos_components) == 2

    def test_spin_channels_present(self) -> None:
        """Both spin channels are represented in the DOS components."""
        spins = {c.spin for c in self.r.dos_components}
        assert spins == {"up", "down"}

    def test_component_index(self) -> None:
        """All components carry component_index 1 for a single-site calculation."""
        for comp in self.r.dos_components:
            assert comp.component_index == 1

    def test_component_energy_is_array(self) -> None:
        """The energy axis is a non-empty NumPy array."""
        comp = self.r.dos_components[0]
        assert isinstance(comp.energy, np.ndarray)
        assert len(comp.energy) > 0

    def test_component_total_shape_matches_energy(self) -> None:
        """Total DOS array length equals the energy axis length for every component."""
        for comp in self.r.dos_components:
            assert comp.total.shape == comp.energy.shape

    def test_component_element_fe(self) -> None:
        """Every component's element property is 'Fe'."""
        for comp in self.r.dos_components:
            assert comp.element == "Fe"

    def test_total_up_parsed(self) -> None:
        """Total spin-up DOS curve is present and labelled correctly."""
        assert self.r.total_up is not None
        assert isinstance(self.r.total_up, DOSCurve)
        assert self.r.total_up.spin == "up"

    def test_total_down_parsed(self) -> None:
        """Total spin-down DOS curve is present and labelled correctly."""
        assert self.r.total_down is not None
        assert self.r.total_down.spin == "down"

    def test_integrated_up_parsed(self) -> None:
        """Integrated spin-up DOS curve is present and labelled correctly."""
        assert self.r.integrated_up is not None
        assert self.r.integrated_up.spin == "up"

    def test_integrated_down_parsed(self) -> None:
        """Integrated spin-down DOS curve is present and labelled correctly."""
        assert self.r.integrated_down is not None
        assert self.r.integrated_down.spin == "down"

    def test_total_curve_energy_length(self) -> None:
        """Energy and values arrays of the total DOS curve have equal length."""
        up = self.r.total_up
        assert up is not None
        assert len(up.energy) > 0
        assert len(up.energy) == len(up.values)


class TestNiDOS:
    """Integration tests for the Ni FCC DOS file."""

    @pytest.fixture(autouse=True)
    def result(self, ni_dos: Path) -> None:
        """Parse the Ni DOS fixture for each test."""
        self.r: DOSResult = parse_dos(ni_dos)

    def test_ncmpx(self) -> None:
        """Input params reflect a single-component Ni calculation."""
        assert self.r.input_params.ncmpx == 1

    def test_two_components(self) -> None:
        """One component times two spin channels yields two DOS components."""
        assert len(self.r.dos_components) == 2

    def test_component_symbol(self) -> None:
        """Every component carries the chemical symbol 'Ni'."""
        for comp in self.r.dos_components:
            assert comp.symbol == "Ni"

    def test_f_orbital_absent(self) -> None:
        """The f-orbital channel is None for Ni (d-band metal, lmxtyp < 3)."""
        for comp in self.r.dos_components:
            assert comp.f is None


class TestNiFeDOS:
    """Integration tests for the NiFe CPA alloy DOS file."""

    @pytest.fixture(autouse=True)
    def result(self, nife_dos: Path) -> None:
        """Parse the NiFe DOS fixture for each test."""
        self.r: DOSResult = parse_dos(nife_dos)

    def test_ncmpx(self) -> None:
        """Input params reflect two CPA components."""
        assert self.r.input_params.ncmpx == 2

    def test_four_components(self) -> None:
        """Two CPA components times two spin channels yields four DOS components."""
        assert len(self.r.dos_components) == 4

    def test_both_elements_present(self) -> None:
        """Both Ni and Fe chemical symbols appear in the component set."""
        symbols = {c.symbol for c in self.r.dos_components}
        assert "Ni" in symbols
        assert "Fe" in symbols

    def test_labels_include_type_prefix(self) -> None:
        """CPA component labels include a colon-separated type:symbol prefix."""
        labels = {c.label for c in self.r.dos_components}
        assert any(":" in label for label in labels)


class TestGaAsDOS:
    """Integration tests for the GaAs compound DOS file."""

    @pytest.fixture(autouse=True)
    def result(self, gaas_dos: Path) -> None:
        """Parse the GaAs DOS fixture for each test."""
        self.r: DOSResult = parse_dos(gaas_dos)

    def test_ncmpx(self) -> None:
        """Input params reflect four components for the GaAs compound."""
        assert self.r.input_params.ncmpx == 4

    def test_components_parsed(self) -> None:
        """At least four type components are parsed for the non-magnetic GaAs run."""
        assert len(self.r.dos_components) >= 4

    def test_ga_and_as_present(self) -> None:
        """Both Ga and As chemical symbols appear in the component set."""
        symbols = {c.symbol for c in self.r.dos_components}
        assert "Ga" in symbols
        assert "As" in symbols


class TestParseDOSComponentsMissingSection:
    """parse_dos_components raises ParseError when the DOS block is absent."""

    def test_raises_on_missing_dos_block(self) -> None:
        """ParseError is raised when no 'DOS of component' headers are found."""
        with pytest.raises(ParseError, match="Missing required section"):
            parse_dos_components(["no DOS blocks here"], ncmpx=1, atom_types=[])


class TestParseCurveBlock:
    """Unit tests for parse_curve_block."""

    def test_returns_none_when_absent(self) -> None:
        """Returns None when the marker pattern is not found in the lines."""
        lines = ["some line", "another line"]
        result = parse_curve_block(lines, r"^ total DOS", 0, spin="up")
        assert result is None

    def test_returns_none_when_occurrence_exceeds_count(self) -> None:
        """Returns None when the requested occurrence index exceeds the match count."""
        lines = [" total DOS", "  -0.5  1.0", "  0.0   2.0"]
        result = parse_curve_block(lines, r"total DOS", 1, spin="up")
        assert result is None

    def test_returns_dos_curve(self) -> None:
        """Returns a DOSCurve with the correct spin label and energy length."""
        lines = [" total DOS", "  -0.5  1.0", "  0.0   2.0", ""]
        result = parse_curve_block(lines, r"total DOS", 0, spin="up")
        assert isinstance(result, DOSCurve)
        assert result.spin == "up"
        assert len(result.energy) == 2

    def test_raises_on_non_two_column_block(self) -> None:
        """ParseError is raised when a data row has more than two columns."""
        lines = [" total DOS", "  -0.5  1.0  0.5", ""]
        with pytest.raises(ParseError, match="Malformed"):
            parse_curve_block(lines, r"total DOS", 0, spin="up")


class TestCollectComponents:
    """Unit tests for collect_components."""

    def test_skips_header_without_match(self) -> None:
        """Lines that do not match the 'DOS of component N' pattern are skipped."""
        lines = ["not a dos header", "  -0.5  1.0  2.0  3.0  4.0"]
        result = collect_components(lines, [0], "up", [])
        assert result == []

    def test_skips_block_with_too_few_columns(self) -> None:
        """Numeric blocks with fewer than four columns are silently skipped."""
        lines = [" DOS of component 1", "  -0.5  1.0"]
        result = collect_components(lines, [0], "up", [])
        assert result == []
