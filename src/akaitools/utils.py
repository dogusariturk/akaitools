"""Unit-conversion utilities."""

from __future__ import annotations

import dataclasses
from typing import Any

import numpy as np

# 1 Rydberg in eV — CODATA 2018 (https://physics.nist.gov/cgi-bin/cuu/Value?rydhcev)
RY_TO_EV: float = 13.605693


def to_serializable(obj: Any) -> Any:
    """Recursively convert a value into a JSON-serializable representation.

    Dataclass instances, lists/tuples, dicts, and ``numpy.ndarray`` values are
    converted recursively; plain JSON-safe types are passed through unchanged.

    Args:
        obj: Value to convert.

    Returns:
        A JSON-serializable representation of ``obj``.
    """
    if dataclasses.is_dataclass(obj):
        return {f.name: to_serializable(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {key: to_serializable(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_serializable(item) for item in obj]
    return obj


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
