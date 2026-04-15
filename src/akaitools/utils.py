"""Unit-conversion utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

# 1 Rydberg in eV — CODATA 2018 (https://physics.nist.gov/cgi-bin/cuu/Value?rydhcev)
RY_TO_EV: float = 13.605693


def ry_to_ev(values: np.ndarray) -> np.ndarray:
    """Convert energy-axis values from Ry to eV.

    Args:
        values: Array of values in Ry.

    Returns:
        Array of values in eV.
    """
    return values * RY_TO_EV


def dos_ry_to_ev(values: np.ndarray) -> np.ndarray:
    """Convert DOS density from states/Ry to states/eV, preserving the integral.

    Args:
        values: DOS array in states/Ry/cell.

    Returns:
        DOS array in states/eV/cell.
    """
    return values / RY_TO_EV
