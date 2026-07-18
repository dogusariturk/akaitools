"""Tests for akaitools.cli."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from akaitools.cli import app

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

runner = CliRunner()


class TestGoCLI:
    """Tests for the 'go' subcommand."""

    def test_go_plain_output_converged(self, fe_go: Path) -> None:
        """Plain text output includes 'yes' for a converged run."""
        result = runner.invoke(app, ["go", str(fe_go)])
        assert result.exit_code == 0
        assert "yes" in result.output

    def test_go_plain_output_not_converged(self, fe_noconv_go: Path) -> None:
        """Plain text output includes 'NO' when the SCF loop never converges."""
        result = runner.invoke(app, ["go", str(fe_noconv_go)])
        assert result.exit_code == 0
        assert "NO" in result.output

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


class TestPlotDosCLI:
    """Tests for the 'plot dos' subcommand."""

    def test_plot_dos_creates_output_file(self, fe_dos: Path, tmp_path: Path) -> None:
        """The plot dos command writes a nonempty image file."""
        output = tmp_path / "dos.png"
        result = runner.invoke(app, ["plot", "dos", str(fe_dos), "-o", str(output)])
        assert result.exit_code == 0
        assert output.exists()
        assert output.stat().st_size > 0

    def test_plot_dos_default_output_path(self, fe_dos: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without -o, the plot dos command writes '<file stem>.png' in the cwd."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["plot", "dos", str(fe_dos)])
        assert result.exit_code == 0
        expected = tmp_path / f"{fe_dos.stem}.png"
        assert expected.exists()
        assert expected.stat().st_size > 0

    def test_plot_dos_with_options(self, fe_dos: Path, tmp_path: Path) -> None:
        """The plot dos command accepts component, spin, orbitals, energy-unit, ef, and no-system-total."""
        output = tmp_path / "dos.png"
        result = runner.invoke(
            app,
            [
                "plot",
                "dos",
                str(fe_dos),
                "--component",
                "1",
                "--spin",
                "up",
                "--orbitals",
                "total,d",
                "--energy-unit",
                "eV",
                "--ef",
                "0.5",
                "--no-system-total",
                "-o",
                str(output),
            ],
        )
        assert result.exit_code == 0
        assert output.exists()
        assert output.stat().st_size > 0

    def test_plot_dos_invalid_spin_exits_nonzero(self, fe_dos: Path, tmp_path: Path) -> None:
        """An invalid --spin value causes a non-zero exit code."""
        output = tmp_path / "dos.png"
        result = runner.invoke(app, ["plot", "dos", str(fe_dos), "--spin", "sideways", "-o", str(output)])
        assert result.exit_code != 0
        assert not output.exists()

    def test_plot_dos_invalid_energy_unit_exits_nonzero(self, fe_dos: Path, tmp_path: Path) -> None:
        """An invalid --energy-unit value causes a non-zero exit code."""
        output = tmp_path / "dos.png"
        result = runner.invoke(app, ["plot", "dos", str(fe_dos), "--energy-unit", "J", "-o", str(output)])
        assert result.exit_code != 0
        assert not output.exists()

    def test_plot_dos_nonexistent_file_exits_nonzero(self, tmp_path: Path) -> None:
        """A missing DOS file causes a non-zero exit code."""
        result = runner.invoke(app, ["plot", "dos", str(tmp_path / "no_such.dos")])
        assert result.exit_code != 0


class TestPlotScfCLI:
    """Tests for the 'plot scf' subcommand."""

    def test_plot_scf_creates_output_file(self, fe_go: Path, tmp_path: Path) -> None:
        """The plot scf command writes a nonempty image file."""
        output = tmp_path / "scf.png"
        result = runner.invoke(app, ["plot", "scf", str(fe_go), "-o", str(output)])
        assert result.exit_code == 0
        assert output.exists()
        assert output.stat().st_size > 0

    def test_plot_scf_default_output_path(self, fe_go: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without -o, the plot scf command writes '<file stem>.png' in the cwd."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["plot", "scf", str(fe_go)])
        assert result.exit_code == 0
        expected = tmp_path / f"{fe_go.stem}.png"
        assert expected.exists()
        assert expected.stat().st_size > 0

    def test_plot_scf_with_field(self, fe_go: Path, tmp_path: Path) -> None:
        """The plot scf command accepts a --field override."""
        output = tmp_path / "scf.png"
        result = runner.invoke(app, ["plot", "scf", str(fe_go), "--field", "moment", "-o", str(output)])
        assert result.exit_code == 0
        assert output.exists()
        assert output.stat().st_size > 0

    def test_plot_scf_invalid_field_exits_nonzero(self, fe_go: Path, tmp_path: Path) -> None:
        """An invalid --field value causes a non-zero exit code."""
        output = tmp_path / "scf.png"
        result = runner.invoke(app, ["plot", "scf", str(fe_go), "--field", "bogus", "-o", str(output)])
        assert result.exit_code != 0
        assert not output.exists()

    def test_plot_scf_nonexistent_file_exits_nonzero(self, tmp_path: Path) -> None:
        """A missing GO file causes a non-zero exit code."""
        result = runner.invoke(app, ["plot", "scf", str(tmp_path / "no_such.out")])
        assert result.exit_code != 0


class TestPlotBsfCLI:
    """Tests for the 'plot bsf' subcommand."""

    def test_plot_bsf_creates_output_file(self, fe_spc: Path, tmp_path: Path) -> None:
        """The plot bsf command writes a nonempty image file."""
        output = tmp_path / "bsf.png"
        result = runner.invoke(app, ["plot", "bsf", str(fe_spc), "--base-dir", str(fe_spc.parent.parent), "-o", str(output)])
        assert result.exit_code == 0
        assert output.exists()
        assert output.stat().st_size > 0

    def test_plot_bsf_default_output_path(self, fe_spc: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without -o, the plot bsf command writes '<file stem>.png' in the cwd."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["plot", "bsf", str(fe_spc), "--base-dir", str(fe_spc.parent.parent)])
        assert result.exit_code == 0
        expected = tmp_path / f"{fe_spc.stem}.png"
        assert expected.exists()
        assert expected.stat().st_size > 0

    def test_plot_bsf_with_options(self, fe_spc: Path, tmp_path: Path) -> None:
        """The plot bsf command accepts spin, ef, energy-unit, cmap, and vmax."""
        output = tmp_path / "bsf.png"
        result = runner.invoke(
            app,
            [
                "plot",
                "bsf",
                str(fe_spc),
                "--base-dir",
                str(fe_spc.parent.parent),
                "--spin",
                "up",
                "--ef",
                "0.5",
                "--energy-unit",
                "eV",
                "--cmap",
                "inferno",
                "--vmax",
                "1.0",
                "-o",
                str(output),
            ],
        )
        assert result.exit_code == 0
        assert output.exists()
        assert output.stat().st_size > 0

    def test_plot_bsf_no_spectral_data_still_succeeds(self, li_spc: Path, tmp_path: Path) -> None:
        """A file with no spectral data still produces a placeholder image."""
        output = tmp_path / "bsf.png"
        result = runner.invoke(app, ["plot", "bsf", str(li_spc), "-o", str(output)])
        assert result.exit_code == 0
        assert output.exists()
        assert output.stat().st_size > 0

    def test_plot_bsf_non_spin_polarized_with_base_dir_succeeds(self, li_spc: Path, tmp_path: Path) -> None:
        """A non-magnetic result with --base-dir auto-discovers only the up channel."""
        output = tmp_path / "bsf.png"
        result = runner.invoke(app, ["plot", "bsf", str(li_spc), "--base-dir", str(li_spc.parent.parent), "-o", str(output)])
        assert result.exit_code == 0
        assert output.exists()
        assert output.stat().st_size > 0

    def test_plot_bsf_invalid_spin_exits_nonzero(self, fe_spc: Path, tmp_path: Path) -> None:
        """An invalid --spin value causes a non-zero exit code."""
        output = tmp_path / "bsf.png"
        result = runner.invoke(
            app, ["plot", "bsf", str(fe_spc), "--base-dir", str(fe_spc.parent.parent), "--spin", "sideways", "-o", str(output)]
        )
        assert result.exit_code != 0
        assert not output.exists()

    def test_plot_bsf_invalid_energy_unit_exits_nonzero(self, fe_spc: Path, tmp_path: Path) -> None:
        """An invalid --energy-unit value causes a non-zero exit code."""
        output = tmp_path / "bsf.png"
        result = runner.invoke(
            app, ["plot", "bsf", str(fe_spc), "--base-dir", str(fe_spc.parent.parent), "--energy-unit", "J", "-o", str(output)]
        )
        assert result.exit_code != 0
        assert not output.exists()

    def test_plot_bsf_nonexistent_file_exits_nonzero(self, tmp_path: Path) -> None:
        """A missing SPC file causes a non-zero exit code."""
        result = runner.invoke(app, ["plot", "bsf", str(tmp_path / "no_such.spc")])
        assert result.exit_code != 0
