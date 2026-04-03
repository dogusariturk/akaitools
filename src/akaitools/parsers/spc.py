"""Parser for AkaiKKR SPC (Bloch Spectral Function) output files."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from akaitools.errors import ParseError
from akaitools.models import (
    KMeshInfo,
    SPCParams,
    SPCResult,
    SpectralFunction,
)
from akaitools.parsers.common import (
    parse_common_sections,
    read_lines,
    require_line,
)
from akaitools.parsers.go import parse_iterations

_SPMAIN_EW_EZ_RX = re.compile(r"ew=\s*([\d.]+)\s+ez=\s*([\d.]+)")
_SPMAIN_PRETA_RX = re.compile(r"preta=\s*([\d.]+)\s+eta=\s*([\d.]+)")
_SPMAIN_SYMOP_RX = re.compile(r"symop\s+(.+)")
_SPMAIN_LAST_RX = re.compile(
    r"last=\s*(\d+)\s+np=\s*(\d+)\s+ngpt=\s*(\d+)"
    r"\s+nrpt=\s*(\d+)\s+nk=\s*(\d+)\s+nd=\s*(\d+)"
)
_SPC_HEADER2_RX = re.compile(r"#\s+([-\d.E+]+)\s+([-\d.E+]+)\s+(\d+)\s+(\d+)")
_SPC_KLABEL_RX = re.compile(r"(\d+)\s+'([^']+)'")


def parse_spc_params(lines: list[str]) -> SPCParams:
    """Parse the ``***msg in spmain`` block.

    Args:
        lines: Full file content split into lines.

    Returns:
        The parsed SPC-specific parameters.

    Raises:
        ParseError: If the spmain block is missing or any field cannot be parsed.
    """
    anchor = require_line(lines, r"\*\*\*msg in spmain", section="***msg in spmain block")

    # Search a window of up to 10 lines after the anchor for each value
    window = "\n".join(lines[anchor : anchor + 10])

    ew_ez = _SPMAIN_EW_EZ_RX.search(window)
    if ew_ez is None:
        raise ParseError("Missing ew/ez values in spmain block")
    preta = _SPMAIN_PRETA_RX.search(window)
    if preta is None:
        raise ParseError("Missing preta/eta values in spmain block")
    symop = _SPMAIN_SYMOP_RX.search(window)
    if symop is None:
        raise ParseError("Missing symop line in spmain block")
    last = _SPMAIN_LAST_RX.search(window)
    if last is None:
        raise ParseError("Missing last/np/ngpt/nrpt/nk/nd values in spmain block")

    symop_labels = tuple(symop.group(1).split())

    return SPCParams(
        ew=float(ew_ez.group(1)),
        ez=float(ew_ez.group(2)),
        preta=float(preta.group(1)),
        eta=float(preta.group(2)),
        symop_labels=symop_labels,
        last=int(last.group(1)),
        np=int(last.group(2)),
        ngpt=int(last.group(3)),
        nrpt=int(last.group(4)),
        nk=int(last.group(5)),
        nd=int(last.group(6)),
    )


def parse_spectral_function_header(lines: list[str]) -> KMeshInfo:
    """Parse the 4-line header of a spectral function data file.

    Args:
        lines: At least the first 4 lines of the spectral function file.

    Returns:
        The parsed k-mesh and energy-mesh metadata.

    Raises:
        ParseError: If the header is missing or malformed.
    """
    if len(lines) < 4:
        raise ParseError("Spectral function file is too short to contain a valid header")
    if lines[0].strip() != "### header for format (c)":
        raise ParseError(f"Expected '### header for format (c)', got: {lines[0].strip()!r}")
    if lines[3].strip() != "### end of header":
        raise ParseError(f"Expected '### end of header', got: {lines[3].strip()!r}")

    match = _SPC_HEADER2_RX.search(lines[1])
    if match is None:
        raise ParseError(f"Cannot parse spectral function header line: {lines[1].strip()!r}")

    energy_min = float(match.group(1))
    energy_max = float(match.group(2))
    n_energy = int(match.group(3))
    n_sym_points = int(match.group(4))

    high_symmetry_indices: dict[int, str] = {}
    if n_sym_points > 0:
        for idx_str, label in _SPC_KLABEL_RX.findall(lines[2]):
            high_symmetry_indices[int(idx_str)] = label

    return KMeshInfo(
        energy_min=energy_min,
        energy_max=energy_max,
        n_energy=n_energy,
        n_sym_points=n_sym_points,
        high_symmetry_indices=high_symmetry_indices,
    )


def parse_spectral_function(path: Path | str, spin: str) -> SpectralFunction:
    """Parse a spectral function data file (``*_up.spc`` or ``*_dn.spc``).

    Args:
        path: Path to the spectral function data file.
        spin: Spin channel label — ``"up"`` or ``"down"``.

    Returns:
        The parsed spectral function. ``data`` is ``None`` when
        ``n_sym_points == 0`` (no k-path was computed).

    Raises:
        ParseError: If the file header is malformed or the data matrix
            has an unexpected shape.
    """
    lines = read_lines(path)
    kmesh = parse_spectral_function_header(lines[:4])

    if kmesh.n_sym_points == 0:
        return SpectralFunction(spin=spin, kmesh=kmesh, data=None)

    rows: list[list[float]] = []
    for line in lines[4:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        rows.append([float(v) for v in stripped.split()])

    if not rows:
        raise ParseError(f"Spectral function file declares {kmesh.n_sym_points} high-symmetry points but contains no data rows")

    data = np.array(rows, dtype=np.float64)
    if data.shape[0] != kmesh.n_energy:
        raise ParseError(f"Spectral function data has {data.shape[0]} energy rows; expected {kmesh.n_energy} from header")

    return SpectralFunction(spin=spin, kmesh=kmesh, data=data)


def _resolve_spectral_path(
    base: Path,
    file_stem: str,
    suffix: str,
    override: Path | str | None,
) -> Path | None:
    """Return the resolved data file path, or ``None`` if not found.

    Args:
        base: Root directory for resolving ``file_stem``.
        file_stem: Base path from ``input_params.file`` (e.g. ``"data/fe"``).
        suffix: Spin suffix — ``"up"`` or ``"dn"``.
        override: Explicit path that, when provided, bypasses auto-discovery.

    Returns:
        The resolved path, or ``None`` if the candidate does not exist.
    """
    if override is not None:
        return Path(override)
    candidate = base / f"{file_stem}_{suffix}.spc"
    return candidate if candidate.exists() else None


class SPCParser:
    """Parse AkaiKKR SPC output files."""

    def parse(
        self,
        path: Path | str,
        *,
        base_dir: Path | str | None = None,
        data_up: Path | str | None = None,
        data_down: Path | str | None = None,
    ) -> SPCResult:
        """Parse an AkaiKKR SPC log file and optional spectral function data.

        Spectral function data files (``*_up.spc``, ``*_dn.spc``) are located
        automatically by appending ``_up.spc`` / ``_dn.spc`` to
        ``input_params.file`` and resolving from ``base_dir``. Supply
        ``data_up`` or ``data_down`` to override either path explicitly.

        Args:
            path: Path to the SPC log file.
            base_dir: Directory from which ``input_params.file`` is resolved
                to auto-locate the spectral function data files. Defaults to
                the log file's parent directory.
            data_up: Explicit path to the spin-up spectral function data file;
                overrides auto-discovery.
            data_down: Explicit path to the spin-down spectral function data
                file; overrides auto-discovery.

        Returns:
            The parsed SPC result. ``spectral_up`` / ``spectral_down`` are
            ``None`` when their data files cannot be found.

        Raises:
            ParseError: If the log file is missing required sections.
        """
        lines = read_lines(path)
        common = parse_common_sections(lines)
        spc_params = parse_spc_params(lines)

        iterations = parse_iterations(lines)
        iteration = iterations[0] if iterations else None

        root = Path(base_dir) if base_dir is not None else Path(path).parent
        up_path = _resolve_spectral_path(root, common.input_params.file, "up", data_up)
        dn_path = _resolve_spectral_path(root, common.input_params.file, "dn", data_down)

        return SPCResult(
            date=common.header.date,
            time=common.header.time,
            meshr=common.header.meshr,
            mse=common.header.mse,
            ng=common.header.ng,
            mxl=common.header.mxl,
            input_params=common.input_params,
            energy_mesh=common.energy_mesh,
            lattice=common.lattice,
            atom_types=common.atom_types,
            positions=common.positions,
            core_configs=common.core_configs,
            atomic_properties=common.atomic_properties,
            system_info=common.system_info,
            spc_params=spc_params,
            iteration=iteration,
            spectral_up=parse_spectral_function(up_path, "up") if up_path is not None else None,
            spectral_down=parse_spectral_function(dn_path, "down") if dn_path is not None else None,
        )
