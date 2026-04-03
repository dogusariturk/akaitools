"""Tests for akaitools.parsers.common."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from akaitools.errors import ParseError
from akaitools.parsers.common import (
    ATOMIC_SYMBOLS,
    find_all_lines,
    find_line,
    parse_common_sections,
    parse_header,
    read_lines,
    require_line,
    scan_numeric_block,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_atomic_symbols_iron() -> None:
    """ATOMIC_SYMBOLS maps Z=26 to 'Fe'."""
    assert ATOMIC_SYMBOLS[26] == "Fe"


def test_atomic_symbols_oganesson() -> None:
    """ATOMIC_SYMBOLS includes Z=118 (Oganesson)."""
    assert ATOMIC_SYMBOLS[118] == "Og"


def test_atomic_symbols_hydrogen() -> None:
    """ATOMIC_SYMBOLS starts at Z=1 (Hydrogen)."""
    assert ATOMIC_SYMBOLS[1] == "H"


def test_find_line_found() -> None:
    """find_line returns the index of the first matching line."""
    lines = ["apple", "banana", "cherry"]
    assert find_line(lines, r"ban") == 1


def test_find_line_not_found() -> None:
    """find_line returns -1 when no line matches."""
    lines = ["apple", "banana"]
    assert find_line(lines, r"xyz") == -1


def test_find_line_with_start_offset() -> None:
    """find_line respects the start offset."""
    lines = ["match", "no", "match"]
    assert find_line(lines, r"match", start=1) == 2


def test_find_all_lines_multiple_matches() -> None:
    """find_all_lines returns all matching line indices."""
    lines = ["aa", "bb", "aa", "cc"]
    assert find_all_lines(lines, r"aa") == [0, 2]


def test_find_all_lines_no_match() -> None:
    """find_all_lines returns an empty list when there are no matches."""
    assert find_all_lines(["foo", "bar"], r"xyz") == []


def test_require_line_found() -> None:
    """require_line returns the correct index when the section exists."""
    lines = ["header", "data read in", "more"]
    assert require_line(lines, r"data read in", section="data read in") == 1


def test_require_line_missing_raises() -> None:
    """require_line raises ParseError when the section is absent."""
    with pytest.raises(ParseError, match="Missing required section"):
        require_line(["nothing"], r"data read in", section="data read in")


def test_scan_numeric_block_reads_values() -> None:
    """scan_numeric_block collects a block of float rows below a header."""
    lines = ["header", "  1.0  2.0  3.0", "  4.0  5.0  6.0", ""]
    rows = scan_numeric_block(lines, start=0)
    assert rows == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]


def test_scan_numeric_block_stops_at_blank() -> None:
    """scan_numeric_block stops at the first blank line after numeric data."""
    lines = ["header", "  1.0", "", "  2.0"]
    rows = scan_numeric_block(lines, start=0)
    assert rows == [[1.0]]


def test_scan_numeric_block_empty() -> None:
    """scan_numeric_block returns [] when no numeric lines follow the header."""
    lines = ["header", "text only"]
    rows = scan_numeric_block(lines, start=0)
    assert rows == []


def test_parse_header_too_short_raises() -> None:
    """parse_header raises ParseError on a file with fewer than 4 lines."""
    with pytest.raises(ParseError, match="too short"):
        parse_header(["only", "three", "lines"])


def test_parse_header_malformed_mesh_line_raises() -> None:
    """parse_header raises ParseError when the mesh line has too few values."""
    lines = ["2025/01/01", "00:00:00", "ignored", "only_one_value"]
    with pytest.raises(ParseError, match="malformed"):
        parse_header(lines)


def test_parse_header_reads_mesh_values() -> None:
    """parse_header extracts meshr, mse, ng, mxl from line 4."""
    lines = ["2025/01/01", "00:00:00", "ignored", " 400  35  21   3"]
    h = parse_header(lines)
    assert h.meshr == 400
    assert h.mse == 35
    assert h.ng == 21
    assert h.mxl == 3
    assert h.date == "2025/01/01"


def test_parse_energy_mesh_no_section_returns_empty() -> None:
    """parse_energy_mesh returns [] when there is no complex energy mesh section."""
    from akaitools.parsers.common import parse_energy_mesh

    result = parse_energy_mesh(["no energy mesh here", "just some text"])
    assert result == []


def test_parse_atom_types_returns_empty_when_no_sections() -> None:
    """parse_atom_types returns [] when the required sections are absent."""
    from akaitools.parsers.common import parse_atom_types

    result = parse_atom_types(["unrelated line 1", "unrelated line 2"])
    assert result == []


def test_parse_positions_returns_empty_when_no_section() -> None:
    """parse_positions returns [] when the atoms in unit cell section is absent."""
    from akaitools.parsers.common import parse_positions

    result = parse_positions(["unrelated line", "another line"])
    assert result == []


def test_parse_system_info_returns_empty_when_no_os_line() -> None:
    """parse_system_info returns a zeroed SystemInfo when OS: is not found."""
    from akaitools.parsers.common import parse_system_info

    si = parse_system_info(["no OS line here", "just some text"])
    assert si.os == ""
    assert si.host == ""
    assert si.elapsed_time == 0.0
    assert si.num_cores == 0


def test_extract_raises_when_no_match_and_no_default() -> None:
    """extract() raises ParseError when pattern has no match and default is None."""
    from akaitools.parsers.common import extract

    with pytest.raises(ParseError, match="Could not match required pattern"):
        extract("no bravais here", r"bravais=(\S+)")


def test_extract_returns_default_when_no_match() -> None:
    """extract() returns the default when pattern has no match."""
    from akaitools.parsers.common import extract

    result = extract("no match here", r"bravais=(\S+)", default="fcc")
    assert result == "fcc"


class TestParseCommonSectionsIntegration:
    """Integration tests that parse real fixture files via common.parse_common_sections."""

    @pytest.fixture(autouse=True)
    def sections(self, fe_go: Path) -> None:
        """Parse the Fe GO fixture for each test."""
        lines = read_lines(fe_go)
        self.s = parse_common_sections(lines)

    def test_header_meshr(self) -> None:
        """Parsed header has the expected meshr value."""
        assert self.s.header.meshr == 400

    def test_lattice_bravais(self) -> None:
        """Parsed lattice has the expected Bravais type."""
        assert self.s.lattice.bravais == "bcc"

    def test_atom_types_count(self) -> None:
        """Fe fixture has one atom type."""
        assert len(self.s.atom_types) == 1

    def test_core_configs_z(self) -> None:
        """Core configs contain Z=26 for Fe."""
        atomic_numbers = {c.z for c in self.s.core_configs}
        assert 26 in atomic_numbers

    def test_system_info_os(self) -> None:
        """System info has a non-empty OS string."""
        assert self.s.system_info.os != ""

    def test_system_info_elapsed_time(self) -> None:
        """System info elapsed time is positive."""
        assert self.s.system_info.elapsed_time > 0.0
