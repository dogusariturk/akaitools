"""akaitools public package exports."""

from __future__ import annotations

from typing import TYPE_CHECKING

from akaitools.models import DOSResult, GOResult, SPCResult
from akaitools.parsers.dos import DOSParser
from akaitools.parsers.go import GOParser
from akaitools.parsers.spc import SPCParser

if TYPE_CHECKING:
    from pathlib import Path

__all__ = [
    "DOSParser",
    "DOSResult",
    "GOParser",
    "GOResult",
    "SPCParser",
    "SPCResult",
    "parse_go",
    "parse_dos",
    "parse_spc",
]


def parse_go(path: Path | str) -> GOResult:
    """Parse an AkaiKKR GO output file.

    Args:
        path: Path to the GO output file.

    Returns:
        The parsed GO result.
    """
    return GOParser().parse(path)


def parse_spc(
    path: Path | str,
    *,
    base_dir: Path | str | None = None,
    data_up: Path | str | None = None,
    data_down: Path | str | None = None,
) -> SPCResult:
    """Parse an AkaiKKR SPC output file.

    Spectral function data files (``*_up.spc``, ``*_dn.spc``) are located
    automatically by appending ``_up.spc`` / ``_dn.spc`` to
    ``input_params.file`` and resolving from ``base_dir``.  Supply
    ``data_up`` or ``data_down`` to override either path explicitly.

    Args:
        path: Path to the SPC log file.
        base_dir: Directory from which ``input_params.file`` is resolved to
            auto-locate the spectral function data files.  Defaults to the
            log file's parent directory.
        data_up: Explicit path to the spin-up spectral function data file.
        data_down: Explicit path to the spin-down spectral function data file.

    Returns:
        The parsed SPC result.
    """
    return SPCParser().parse(path, base_dir=base_dir, data_up=data_up, data_down=data_down)


def parse_dos(path: Path | str) -> DOSResult:
    """Parse an AkaiKKR DOS output file.

    Args:
        path: Path to the DOS output file.

    Returns:
        The parsed DOS result.
    """
    return DOSParser().parse(path)
