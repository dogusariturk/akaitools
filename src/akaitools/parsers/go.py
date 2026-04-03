"""Parser for AkaiKKR GO output files."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from akaitools.models import GOIteration, GOResult
from akaitools.parsers.common import parse_common_sections, read_lines

if TYPE_CHECKING:
    from pathlib import Path


class GOParser:
    """Parse AkaiKKR GO output files."""

    def parse(self, path: Path | str) -> GOResult:
        """Parse an AkaiKKR GO output file.

        Args:
            path: Path to the GO output file.

        Returns:
            The parsed GO result.
        """
        lines = read_lines(path)
        common = parse_common_sections(lines)
        iterations = parse_iterations(lines)

        return GOResult(
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
            iterations=iterations,
            converged="*** no convergence" not in "\n".join(lines[max(0, int(len(lines) * 0.8)) :]),
        )


def parse_iterations(lines: list[str]) -> list[GOIteration]:
    """Extract per-iteration convergence data.

    Args:
        lines: Full file content split into lines.

    Returns:
        The parsed iteration records in file order.
    """
    regex = re.compile(
        r"itr=\s*(\d+)\s+neu=\s*([-\d.E+]+)\s+moment=\s*([-\d.E+]+)"
        r"\s+te=\s*([-\d.E+]+)\s+err=\s*([-\d.E+]+)"
    )
    iterations: list[GOIteration] = []
    for line in lines:
        match = regex.search(line)
        if match is None:
            continue
        iterations.append(
            GOIteration(
                iteration=int(match.group(1)),
                neu=float(match.group(2)),
                moment=float(match.group(3)),
                total_energy=float(match.group(4)),
                rms_error=float(match.group(5)),
            )
        )
    return iterations
