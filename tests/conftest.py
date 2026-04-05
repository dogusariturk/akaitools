"""Pytest fixtures pointing to the bundled example data files."""

from __future__ import annotations

from pathlib import Path

import pytest

SAMPLES = Path(__file__).parent / "data"


@pytest.fixture
def fe_go() -> Path:
    """Return the AkaiKKR sample Fe GO output path.

    Returns:
        The path to the fixture file.
    """
    return SAMPLES / "out" / "fe"


@pytest.fixture
def ni_go() -> Path:
    """Return the AkaiKKR sample Ni GO output path.

    Returns:
        The path to the fixture file.
    """
    return SAMPLES / "out" / "ni"


@pytest.fixture
def nife_go() -> Path:
    """Return the AkaiKKR sample NiFe GO output path.

    Returns:
        The path to the fixture file.
    """
    return SAMPLES / "out" / "nife"


@pytest.fixture
def gaas_go() -> Path:
    """Return the AkaiKKR sample GaAs GO output path.

    Returns:
        The path to the fixture file.
    """
    return SAMPLES / "out" / "gaas"


@pytest.fixture
def fe_dos() -> Path:
    """Return the AkaiKKR sample Fe DOS output path.

    Returns:
        The path to the fixture file.
    """
    return SAMPLES / "out" / "fe.dos"


@pytest.fixture
def ni_dos() -> Path:
    """Return the AkaiKKR sample Ni DOS output path.

    Returns:
        The path to the fixture file.
    """
    return SAMPLES / "out" / "ni.dos"


@pytest.fixture
def nife_dos() -> Path:
    """Return the AkaiKKR sample NiFe DOS output path.

    Returns:
        The path to the fixture file.
    """
    return SAMPLES / "out" / "nife.dos"


@pytest.fixture
def fe_spc() -> Path:
    """Return the AkaiKKR sample Fe SPC log output path.

    Returns:
        The path to the fixture file.
    """
    return SAMPLES / "out" / "fe.spc"


@pytest.fixture
def ni_spc() -> Path:
    """Return the AkaiKKR sample Ni SPC log output path.

    Returns:
        The path to the fixture file.
    """
    return SAMPLES / "out" / "ni.spc"


@pytest.fixture
def nife_spc() -> Path:
    """Return the AkaiKKR sample NiFe SPC log output path.

    Returns:
        The path to the fixture file.
    """
    return SAMPLES / "out" / "nife.spc"


@pytest.fixture
def gaas_dos() -> Path:
    """Return the AkaiKKR sample GaAs DOS output path.

    Returns:
        The path to the fixture file.
    """
    return SAMPLES / "out" / "gaas.dos"
