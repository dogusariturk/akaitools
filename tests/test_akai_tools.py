"""Tests for the akaitools public package API (src/akaitools/__init__.py)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import akaitools
from akaitools import (
    DOSParser,
    DOSResult,
    GOParser,
    GOResult,
    SPCParser,
    SPCResult,
    parse_dos,
    parse_go,
    parse_spc,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_all_public_names_exported() -> None:
    """Every name in __all__ is importable from the package."""
    for name in akaitools.__all__:
        assert hasattr(akaitools, name), f"{name!r} missing from akaitools"


def test_parse_functions_callable() -> None:
    """parse_go, parse_dos, parse_spc are callable from the package."""
    assert callable(parse_go)
    assert callable(parse_dos)
    assert callable(parse_spc)


def test_old_scf_aliases_absent() -> None:
    """Removed SCF API aliases must not be present on the package."""
    assert not hasattr(akaitools, "parse_scf")
    assert not hasattr(akaitools, "SCFParser")
    assert not hasattr(akaitools, "SCFResult")
    assert not hasattr(akaitools, "SCFIteration")


def test_parse_error_accessible_from_errors() -> None:
    """ParseError is importable from akaitools.errors."""
    from akaitools.errors import ParseError

    assert issubclass(ParseError, ValueError)


def test_result_classes_exported() -> None:
    """Result classes are importable from the top-level package."""
    assert GOResult is not None
    assert DOSResult is not None
    assert SPCResult is not None


def test_parser_classes_exported() -> None:
    """Parser classes are importable from the top-level package."""
    assert GOParser is not None
    assert DOSParser is not None
    assert SPCParser is not None


def test_parse_spc_with_explicit_data_paths(tmp_path: Path) -> None:
    """parse_spc accepts explicit data_up and data_down path overrides."""
    from pathlib import Path

    samples = Path(__file__).parent / "data"
    spc_log = samples / "out" / "fe.spc"
    up_path = samples / "data" / "fe_up.spc"
    dn_path = samples / "data" / "fe_dn.spc"

    result = parse_spc(spc_log, data_up=up_path, data_down=dn_path)
    assert result.spectral_up is not None
    assert result.spectral_down is not None


def test_model_types_accessible_from_models() -> None:
    """Detailed model types are available via akaitools.models for explicit import."""
    from akaitools.models import (
        AtomType,
        DOSComponent,
        GOIteration,
        SpectralFunction,
    )

    assert AtomType is not None
    assert DOSComponent is not None
    assert GOIteration is not None
    assert SpectralFunction is not None
