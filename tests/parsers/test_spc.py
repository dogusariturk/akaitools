"""Unit tests for the SPC parser and public API exports."""

from __future__ import annotations

from pathlib import Path

import pytest

import akaitools
from akaitools.errors import ParseError
from akaitools.parsers.spc import parse_spc_params, parse_spectral_function, parse_spectral_function_header

SAMPLES = Path(__file__).parent.parent / "data"


class TestSPCExports:
    """Verify SPC symbols are present in the public API."""

    def test_parse_spc_exported(self) -> None:
        """parse_spc is present and callable on the top-level package."""
        assert hasattr(akaitools, "parse_spc")
        assert callable(akaitools.parse_spc)

    def test_spc_parser_exported(self) -> None:
        """SPCParser is exported from the top-level package."""
        assert hasattr(akaitools, "SPCParser")
        assert "SPCParser" in akaitools.__all__

    def test_spc_result_exported(self) -> None:
        """SPCResult is exported from the top-level package."""
        assert hasattr(akaitools, "SPCResult")
        assert "SPCResult" in akaitools.__all__

    def test_detail_types_accessible_from_models(self) -> None:
        """SpectralFunction, KMeshInfo, SPCParams are importable from akaitools.models."""
        from akaitools.models import KMeshInfo, SPCParams, SpectralFunction

        assert SpectralFunction is not None
        assert KMeshInfo is not None
        assert SPCParams is not None


class TestParseSPCParams:
    """Tests for parse_spc_params."""

    _ANCHOR = "***msg in spmain"

    def test_raises_on_missing_spmain_block(self) -> None:
        """A file without a spmain block should raise ParseError."""
        with pytest.raises(ParseError):
            parse_spc_params(["no spmain block here"])

    def test_raises_on_missing_ew_ez(self) -> None:
        """ParseError raised when ew/ez values are absent after the anchor."""
        lines = [self._ANCHOR, "preta= 0.1 eta= 0.2", "symop E C4", "last= 1 np= 2 ngpt= 3 nrpt= 4 nk= 5 nd= 6"]
        with pytest.raises(ParseError, match="Missing ew/ez"):
            parse_spc_params(lines)

    def test_raises_on_missing_preta(self) -> None:
        """ParseError raised when preta/eta values are absent."""
        lines = [self._ANCHOR, "ew= 0.6 ez= 0.7", "symop E C4", "last= 1 np= 2 ngpt= 3 nrpt= 4 nk= 5 nd= 6"]
        with pytest.raises(ParseError, match="Missing preta/eta"):
            parse_spc_params(lines)

    def test_raises_on_missing_symop(self) -> None:
        """ParseError raised when the symop line is absent."""
        lines = [self._ANCHOR, "ew= 0.6 ez= 0.7", "preta= 0.1 eta= 0.2", "last= 1 np= 2 ngpt= 3 nrpt= 4 nk= 5 nd= 6"]
        with pytest.raises(ParseError, match="Missing symop"):
            parse_spc_params(lines)

    def test_raises_on_missing_last_np(self) -> None:
        """ParseError raised when last/np/ngpt/nrpt/nk/nd values are absent."""
        lines = [self._ANCHOR, "ew= 0.6 ez= 0.7", "preta= 0.1 eta= 0.2", "symop E C4"]
        with pytest.raises(ParseError, match="Missing last"):
            parse_spc_params(lines)


class TestParseSpectralFunction:
    """Tests for parse_spectral_function."""

    def test_fe_matrix_is_populated(self) -> None:
        """Fe spectral data is parsed as a populated matrix with 6 labels."""
        sf = parse_spectral_function(SAMPLES / "data" / "fe_up.spc", "up")
        assert sf.spin == "up"
        assert sf.data is not None
        assert sf.data.shape == (200, 300)
        assert sf.kmesh.n_sym_points == 6
        assert sf.kmesh.n_energy == 200
        assert sf.kmesh.high_symmetry_indices == {
            1: "(0 0 0)",
            80: "(0 1 0)",
            136: "(1/2 1/2 0)",
            176: "(1/2 1/2 1/2)",
            244: "(0 0 0)",
            300: "(1/2 1/2 0)",
        }

    def test_populated_matrix_has_correct_shape(self) -> None:
        """NiFe spectral data has 6 sym points and 300 k-columns."""
        sf = parse_spectral_function(SAMPLES / "data" / "nife_up.spc", "up")
        assert sf.data is not None
        assert sf.data.shape[0] == sf.kmesh.n_energy
        assert sf.data.shape[0] == 200

    def test_spin_label_preserved(self) -> None:
        """The spin label passed to parse_spectral_function is stored on the result."""
        sf = parse_spectral_function(SAMPLES / "data" / "fe_dn.spc", "down")
        assert sf.spin == "down"


class TestParseSpectralFunctionHeader:
    """Tests for parse_spectral_function_header error paths."""

    _GOOD_LINES = [
        "### header for format (c)",
        "# -0.5000E+00  0.5000E+00   200   0",
        "",
        "### end of header",
    ]

    def test_raises_on_too_short_file(self) -> None:
        """ParseError raised when file has fewer than 4 lines."""
        with pytest.raises(ParseError, match="too short"):
            parse_spectral_function_header(["only", "three"])

    def test_raises_on_wrong_first_line(self) -> None:
        """ParseError raised when the first line is not the expected header sentinel."""
        bad = ["### wrong header", self._GOOD_LINES[1], self._GOOD_LINES[2], self._GOOD_LINES[3]]
        with pytest.raises(ParseError, match="Expected '### header for format"):
            parse_spectral_function_header(bad)

    def test_raises_on_wrong_end_line(self) -> None:
        """ParseError raised when the fourth line is not '### end of header'."""
        bad = [self._GOOD_LINES[0], self._GOOD_LINES[1], self._GOOD_LINES[2], "### wrong end"]
        with pytest.raises(ParseError, match="Expected '### end of header'"):
            parse_spectral_function_header(bad)

    def test_raises_on_unparseable_header_line(self) -> None:
        """ParseError raised when line 2 doesn't match the expected pattern."""
        bad = [self._GOOD_LINES[0], "# not parseable at all", self._GOOD_LINES[2], self._GOOD_LINES[3]]
        with pytest.raises(ParseError, match="Cannot parse spectral function header"):
            parse_spectral_function_header(bad)

    def test_valid_header_no_sym_points(self) -> None:
        """A valid header with n_sym_points=0 is parsed correctly."""
        from akaitools.models import KMeshInfo

        result = parse_spectral_function_header(self._GOOD_LINES)
        assert isinstance(result, KMeshInfo)
        assert result.n_sym_points == 0
        assert result.n_energy == 200
        assert result.high_symmetry_indices == {}
