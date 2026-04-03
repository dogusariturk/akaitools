"""Tests for akaitools.cli."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from akaitools.cli import app

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


class TestGoCLI:
    """Tests for the 'go' subcommand."""

    def test_go_plain_output_converged(self, fe_go: Path) -> None:
        """Plain text output includes 'yes' for a converged run."""
        result = runner.invoke(app, ["go", str(fe_go)])
        assert result.exit_code == 0
        assert "yes" in result.output

    def test_go_plain_output_lattice(self, fe_go: Path) -> None:
        """Plain text output includes the Bravais lattice type."""
        result = runner.invoke(app, ["go", str(fe_go)])
        assert result.exit_code == 0
        assert "bcc" in result.output

    def test_go_json_is_valid(self, fe_go: Path) -> None:
        """JSON output is valid and contains expected top-level keys."""
        result = runner.invoke(app, ["go", str(fe_go), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "converged" in data
        assert "lattice" in data
        assert "atomic_properties" in data

    def test_go_json_hyperfine_present(self, fe_go: Path) -> None:
        """JSON output includes hyperfine_kG for a magnetic calculation."""
        result = runner.invoke(app, ["go", str(fe_go), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        prop = data["atomic_properties"][0]
        assert prop["hyperfine_kG"] is not None

    def test_go_json_hyperfine_is_float_or_null(self, gaas_go: Path) -> None:
        """JSON output has hyperfine_kG as a float or null — never a non-float."""
        result = runner.invoke(app, ["go", str(gaas_go), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        for prop in data["atomic_properties"]:
            assert prop["hyperfine_kG"] is None or isinstance(prop["hyperfine_kG"], float)

    def test_go_nonexistent_file_exits_nonzero(self, tmp_path: Path) -> None:
        """A missing file causes a non-zero exit code."""
        result = runner.invoke(app, ["go", str(tmp_path / "no_such.out")])
        assert result.exit_code != 0

    def test_go_json_calculation_keys(self, fe_go: Path) -> None:
        """JSON output has a 'calculation' key with functional and relativistic fields."""
        result = runner.invoke(app, ["go", str(fe_go), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "calculation" in data
        assert "functional" in data["calculation"]


class TestDosCLI:
    """Tests for the 'dos' subcommand."""

    def test_dos_plain_output(self, fe_dos: Path) -> None:
        """Plain text output for a DOS file succeeds."""
        result = runner.invoke(app, ["dos", str(fe_dos)])
        assert result.exit_code == 0
        assert "Energy" in result.output

    def test_dos_json_is_valid(self, fe_dos: Path) -> None:
        """JSON output is valid and contains expected keys."""
        result = runner.invoke(app, ["dos", str(fe_dos), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "lattice" in data
        assert "components" in data
        assert "energy_range_Ry" in data

    def test_dos_json_component_filter(self, fe_dos: Path) -> None:
        """The --component flag filters the JSON output to one component index."""
        result = runner.invoke(app, ["dos", str(fe_dos), "--json", "--component", "1"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["components"]) >= 1
        assert all(c["index"] == 1 for c in data["components"])

    def test_dos_nonexistent_file_exits_nonzero(self, tmp_path: Path) -> None:
        """A missing DOS file causes a non-zero exit code."""
        result = runner.invoke(app, ["dos", str(tmp_path / "no_such.dos")])
        assert result.exit_code != 0

    def test_dos_plain_includes_lattice(self, fe_dos: Path) -> None:
        """Plain text output contains the Bravais lattice type."""
        result = runner.invoke(app, ["dos", str(fe_dos)])
        assert result.exit_code == 0
        assert "bcc" in result.output
