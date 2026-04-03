"""Command-line interface for akaitools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import numpy as np
import typer

from akaitools import parse_dos, parse_go, parse_spc
from akaitools.errors import ParseError

if TYPE_CHECKING:
    from akaitools.models import DOSResult, GOResult, SPCResult

app = typer.Typer(help="akaitools — Parse AkaiKKR electronic structure output files.", no_args_is_help=True, add_completion=False)


def _go_summary(result: GOResult) -> dict:
    """Build a compact summary for a parsed GO result.

    Args:
        result: Parsed GO result object.

    Returns:
        A JSON-serializable summary dictionary.
    """
    iters = result.iterations
    last = iters[-1] if iters else None
    return {
        "file_date": result.date,
        "lattice": {
            "bravais": result.lattice.bravais,
            "a_bohr": result.lattice.a,
            "volume_au": result.lattice.volume,
        },
        "calculation": {
            "functional": result.input_params.sdftyp,
            "relativistic": result.input_params.reltyp,
            "ntyp": result.input_params.ntyp,
            "natm": result.input_params.natm,
            "ncmpx": result.input_params.ncmpx,
        },
        "converged": result.converged,
        "n_iterations": len(iters),
        "final_moment_muB": last.moment if last else None,
        "final_energy_Ry": last.total_energy if last else None,
        "atomic_properties": [
            {
                "type": p.type_name,
                "element": p.element,
                "z": p.z,
                "total_charge": p.total_charge,
                "spin_moment_muB": p.spin_moment,
                "orbital_moment_muB": p.orbital_moment,
                "hyperfine_kG": p.hyperfine_field.total if p.hyperfine_field is not None else None,
            }
            for p in result.atomic_properties
        ],
        "timing": {
            "host": result.system_info.host,
            "elapsed_sec": result.system_info.elapsed_time,
            "threads": result.system_info.num_threads,
        },
    }


def _dos_summary(result: DOSResult, component: int | None) -> dict:
    """Build a compact summary for a parsed DOS result.

    Args:
        result: Parsed DOS result object.
        component: Optional component index filter.

    Returns:
        A JSON-serializable summary dictionary.
    """
    comps = result.dos_components
    if component is not None:
        comps = [c for c in comps if c.component_index == component]

    return {
        "file_date": result.date,
        "lattice": {
            "bravais": result.lattice.bravais,
            "a_bohr": result.lattice.a,
        },
        "calculation": {
            "functional": result.input_params.sdftyp,
            "relativistic": result.input_params.reltyp,
            "ncmpx": result.input_params.ncmpx,
        },
        "energy_range_Ry": {
            "min": float(comps[0].energy[0]) if comps else None,
            "max": float(comps[0].energy[-1]) if comps else None,
            "n_points": int(result.mse),
        },
        "components": [
            {
                "index": c.component_index,
                "dos_at_fermi_total": float(c.total[int(np.argmin(np.abs(c.energy)))]),
                "has_f_orbital": c.f is not None,
            }
            for c in comps
        ],
    }


def _spc_summary(result: SPCResult) -> dict:
    """Build a compact summary for a parsed SPC result.

    Args:
        result: Parsed SPC result object.

    Returns:
        A JSON-serializable summary dictionary.
    """
    sp = result.spc_params

    def _spectral_info(sf) -> dict | None:
        if sf is None:
            return None
        km = sf.kmesh
        return {
            "energy_range_Ry": {"min": km.energy_min, "max": km.energy_max},
            "n_energy": km.n_energy,
            "n_sym_points": km.n_sym_points,
            "high_symmetry_points": km.high_symmetry_indices,
            "has_data": sf.data is not None,
        }

    return {
        "file_date": result.date,
        "lattice": {
            "bravais": result.lattice.bravais,
            "a_bohr": result.lattice.a,
            "volume_au": result.lattice.volume,
        },
        "calculation": {
            "functional": result.input_params.sdftyp,
            "relativistic": result.input_params.reltyp,
            "ntyp": result.input_params.ntyp,
            "natm": result.input_params.natm,
            "ncmpx": result.input_params.ncmpx,
        },
        "spc_params": {
            "ew_Ry": sp.ew,
            "ez_Ry": sp.ez,
            "preta": sp.preta,
            "eta_Ry": sp.eta,
            "nk": sp.nk,
            "ngpt": sp.ngpt,
            "nd": sp.nd,
        },
        "moment_muB": result.iteration.moment if result.iteration else None,
        "atomic_properties": [
            {
                "type": p.type_name,
                "element": p.element,
                "z": p.z,
                "total_charge": p.total_charge,
                "spin_moment_muB": p.spin_moment,
                "orbital_moment_muB": p.orbital_moment,
            }
            for p in result.atomic_properties
        ],
        "spectral_up": _spectral_info(result.spectral_up),
        "spectral_down": _spectral_info(result.spectral_down),
        "timing": {
            "host": result.system_info.host,
            "elapsed_sec": result.system_info.elapsed_time,
        },
    }


@app.command("go", no_args_is_help=True)
def go_cmd(
    file: Annotated[Path, typer.Argument(exists=True, help="AkaiKKR GO output file.")],
    as_json: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
) -> None:
    """Parse an AkaiKKR GO output file and print a summary.

    Args:
        file: Path to the GO output file.
        as_json: Whether to emit JSON instead of plain text.

    Returns:
        None.
    """
    try:
        result = parse_go(file)
    except ParseError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None
    summary = _go_summary(result)

    if as_json:
        typer.echo(json.dumps(summary, indent=2))
        return

    lat = summary["lattice"]
    calc = summary["calculation"]
    typer.echo(f"File   : {file}")
    typer.echo(f"Date   : {summary['file_date']}")
    typer.echo(f"Lattice: {lat['bravais']}  a={lat['a_bohr']:.5f} bohr  V={lat['volume_au']:.2f} a.u.")
    typer.echo(f"XC     : {calc['functional']}  reltyp={calc['relativistic']}")
    typer.echo(f"Types  : {calc['ntyp']}   Atoms: {calc['natm']}   Components: {calc['ncmpx']}")
    typer.echo(f"Converged : {'yes' if summary['converged'] else 'NO'}")
    typer.echo(f"Iterations: {summary['n_iterations']}")
    if summary["final_moment_muB"] is not None:
        typer.echo(f"Final moment : {summary['final_moment_muB']:.4f} μB")
        typer.echo(f"Final energy : {summary['final_energy_Ry']:.8f} Ry")
    typer.echo("")
    header = f"{'Type':<20} {'Element':<8} {'Z':>5} {'Charge':>10} {'Spin(μB)':>10} {'Hf(kG)':>10}"
    typer.echo(header)
    typer.echo("-" * 68)
    for p in summary["atomic_properties"]:
        hf = f"{p['hyperfine_kG']:>10.3f}" if p["hyperfine_kG"] is not None else f"{'N/A':>10}"
        typer.echo(
            f"{p['type']:<20} {p['element']:<8} {p['z']:>5.0f} {p['total_charge']:>10.4f} {p['spin_moment_muB']:>10.4f} {hf}"
        )


@app.command("dos", no_args_is_help=True)
def dos_cmd(
    file: Annotated[Path, typer.Argument(exists=True, help="AkaiKKR DOS output file.")],
    as_json: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
    component: Annotated[int | None, typer.Option("--component", "-c", help="Show only this component index.")] = None,
) -> None:
    """Parse an AkaiKKR DOS output file and print a summary.

    Args:
        file: Path to the DOS output file.
        as_json: Whether to emit JSON instead of plain text.
        component: Optional component index filter.

    Returns:
        None.
    """
    try:
        result = parse_dos(file)
    except ParseError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None
    summary = _dos_summary(result, component)

    if as_json:
        typer.echo(json.dumps(summary, indent=2))
        return

    lat = summary["lattice"]
    er = summary["energy_range_Ry"]
    typer.echo(f"File   : {file}")
    typer.echo(f"Date   : {summary['file_date']}")
    typer.echo(f"Lattice: {lat['bravais']}  a={lat['a_bohr']:.5f} bohr")
    typer.echo(f"Energy : [{er['min']:.4f}, {er['max']:.4f}] Ry  ({er['n_points']} points)")
    typer.echo("")
    typer.echo(f"{'Comp':>6} {'DOS@Ef':>12} {'f-orbital':>10}")
    typer.echo("-" * 32)
    for c in summary["components"]:
        typer.echo(f"{c['index']:>6} {c['dos_at_fermi_total']:>12.4f} {'yes' if c['has_f_orbital'] else 'no':>10}")


@app.command("spc", no_args_is_help=True)
def spc_cmd(
    file: Annotated[Path, typer.Argument(exists=True, help="AkaiKKR SPC output file.")],
    as_json: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
    base_dir: Annotated[
        Path | None, typer.Option("--base-dir", "-b", help="Directory for resolving spectral data files.")
    ] = None,
    data_up: Annotated[Path | None, typer.Option("--data-up", help="Explicit path to spin-up spectral data file.")] = None,
    data_down: Annotated[Path | None, typer.Option("--data-down", help="Explicit path to spin-down spectral data file.")] = None,
) -> None:
    """Parse an AkaiKKR SPC output file and print a summary.

    Args:
        file: Path to the SPC output file.
        as_json: Whether to emit JSON instead of plain text.
        base_dir: Directory for resolving spectral data files.
        data_up: Explicit path to spin-up spectral data file.
        data_down: Explicit path to spin-down spectral data file.

    Returns:
        None.
    """
    try:
        result = parse_spc(file, base_dir=base_dir, data_up=data_up, data_down=data_down)
    except ParseError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None
    summary = _spc_summary(result)

    if as_json:
        typer.echo(json.dumps(summary, indent=2))
        return

    lat = summary["lattice"]
    calc = summary["calculation"]
    sp = summary["spc_params"]
    typer.echo(f"File   : {file}")
    typer.echo(f"Date   : {summary['file_date']}")
    typer.echo(f"Lattice: {lat['bravais']}  a={lat['a_bohr']:.5f} bohr  V={lat['volume_au']:.2f} a.u.")
    typer.echo(f"XC     : {calc['functional']}  reltyp={calc['relativistic']}")
    typer.echo(f"Types  : {calc['ntyp']}   Atoms: {calc['natm']}   Components: {calc['ncmpx']}")
    typer.echo(f"SPC    : ew={sp['ew_Ry']:.4f} Ry  ez={sp['ez_Ry']:.4f} Ry  eta={sp['eta_Ry']:.4f} Ry")
    typer.echo(f"k-mesh : nk={sp['nk']}  ngpt={sp['ngpt']}  nd={sp['nd']}")
    if summary["moment_muB"] is not None:
        typer.echo(f"Moment : {summary['moment_muB']:.4f} μB")
    typer.echo("")

    for label, sf in [("spin-up", summary["spectral_up"]), ("spin-down", summary["spectral_down"])]:
        if sf is None:
            typer.echo(f"Spectral ({label}): data file not found")
            continue
        er = sf["energy_range_Ry"]
        typer.echo(
            f"Spectral ({label}): [{er['min']:.4f}, {er['max']:.4f}] Ry  {sf['n_energy']} energy pts  {sf['n_sym_points']} sym-pts"
        )
        if sf["high_symmetry_points"]:
            labels = "  ".join(f"{k}:{v}" for k, v in sf["high_symmetry_points"].items())
            typer.echo(f"  k-labels: {labels}")

    typer.echo("")
    header = f"{'Type':<20} {'Element':<8} {'Z':>5} {'Charge':>10} {'Spin(μB)':>10}"
    typer.echo(header)
    typer.echo("-" * 57)
    for p in summary["atomic_properties"]:
        typer.echo(f"{p['type']:<20} {p['element']:<8} {p['z']:>5.0f} {p['total_charge']:>10.4f} {p['spin_moment_muB']:>10.4f}")


def main() -> None:
    """Run the Typer application.

    Returns:
        None.
    """
    app()
