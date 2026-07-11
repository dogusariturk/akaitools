"""Models for AkaiKKR GO (self-consistent field) results."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from akaitools.models.common import CalculationResult
from akaitools.utils import RY_TO_EV


@dataclass(frozen=True)
class GOIteration:
    """Data from one self-consistent field iteration."""

    iteration: int
    neu: float  # charge neutrality
    moment: float  # Total magnetic moment (μB)
    total_energy: float  # Total energy (Ry)
    rms_error: float  # Log10 of RMS error

    @property
    def total_energy_ev(self) -> float:
        """Total energy in eV.

        Returns:
            Total energy converted from Ry to eV.
        """
        return self.total_energy * RY_TO_EV


@dataclass(frozen=True)
class GOResult(CalculationResult):
    """Parsed result from an AkaiKKR GO output file."""

    iterations: list[GOIteration]
    converged: bool

    def to_dataframe(self) -> pd.DataFrame:
        """Convert SCF iteration history to a pandas DataFrame.

        Returns:
            A DataFrame with one row per iteration and columns for iteration
            number, charge neutrality, magnetic moment, total energy, and
            RMS error.
        """
        if not self.iterations:
            return pd.DataFrame(columns=["neu", "moment", "total_energy_Ry", "total_energy_eV", "rms_error"])
        return pd.DataFrame(
            {
                "neu": [it.neu for it in self.iterations],
                "moment": [it.moment for it in self.iterations],
                "total_energy_Ry": [it.total_energy for it in self.iterations],
                "total_energy_eV": [it.total_energy_ev for it in self.iterations],
                "rms_error": [it.rms_error for it in self.iterations],
            }
        )
