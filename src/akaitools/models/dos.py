"""Models for AkaiKKR DOS results."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from akaitools.models.common import CalculationResult
from akaitools.utils import RY_TO_EV


@dataclass(frozen=True)
class DOSComponent:
    """Density of states for one CPA component and spin channel.

    Attributes:
        component_index: One-based component index from ``DOS of component N``.
        type_name: AkaiKKR site-type name for this component.
        symbol: Chemical element symbol for this component.
        label: User-facing component label. This is ``type_name`` for pure sites
            and ``type_name:symbol`` for CPA-mixed sites.
        spin: Spin channel — ``"up"`` or ``"down"``.
        energy: Real-axis energy points, shape ``(n_points,)``, in Ry.
        s: s-orbital projected DOS in states/Ry/cell, shape ``(n_points,)``.
        p: p-orbital projected DOS in states/Ry/cell.
        d: d-orbital projected DOS in states/Ry/cell.
        total: Total local DOS in states/Ry/cell (sum of all orbital channels).
        f: f-orbital projected DOS in states/Ry/cell; ``None`` when ``lmxtyp < 3``.
    """

    component_index: int
    type_name: str
    symbol: str
    label: str
    spin: str
    energy: np.ndarray
    s: np.ndarray
    p: np.ndarray
    d: np.ndarray
    total: np.ndarray
    f: np.ndarray | None = None

    @property
    def element(self) -> str:
        """Return the chemical symbol.

        Returns:
            The chemical element symbol.
        """
        return self.symbol

    @property
    def energy_ev(self) -> np.ndarray:
        """Energy array in eV.

        Returns:
            Real-axis energy points converted from Ry to eV, shape ``(n_points,)``.
        """
        return self.energy * RY_TO_EV

    @property
    def s_ev(self) -> np.ndarray:
        """s-orbital projected DOS in states/eV/cell.

        Returns:
            s-orbital DOS converted from states/Ry/cell to states/eV/cell.
        """
        return self.s / RY_TO_EV

    @property
    def p_ev(self) -> np.ndarray:
        """p-orbital projected DOS in states/eV/cell.

        Returns:
            p-orbital DOS converted from states/Ry/cell to states/eV/cell.
        """
        return self.p / RY_TO_EV

    @property
    def d_ev(self) -> np.ndarray:
        """d-orbital projected DOS in states/eV/cell.

        Returns:
            d-orbital DOS converted from states/Ry/cell to states/eV/cell.
        """
        return self.d / RY_TO_EV

    @property
    def total_ev(self) -> np.ndarray:
        """Total local DOS in states/eV/cell.

        Returns:
            Total DOS converted from states/Ry/cell to states/eV/cell.
        """
        return self.total / RY_TO_EV

    @property
    def f_ev(self) -> np.ndarray | None:
        """f-orbital projected DOS in states/eV/cell; ``None`` when ``lmxtyp < 3``.

        Returns:
            f-orbital DOS converted from states/Ry/cell to states/eV/cell,
            or ``None`` if f-orbital data is absent.
        """
        return self.f / RY_TO_EV if self.f is not None else None

    def to_dataframe(self) -> pd.DataFrame:
        """Convert this component's DOS data to a pandas DataFrame.

        Returns:
            A DataFrame with one row per energy point and columns for
            component metadata, orbital-resolved DOS, and total DOS.
        """
        return pd.DataFrame(
            {
                "component_index": self.component_index,
                "type_name": self.type_name,
                "symbol": self.symbol,
                "label": self.label,
                "element": self.symbol,
                "energy_Ry": self.energy,
                "energy_eV": self.energy_ev,
                "s": self.s,
                "p": self.p,
                "d": self.d,
                "f": self.f if self.f is not None else np.zeros(len(self.energy)),
                "total": self.total,
            }
        )


@dataclass(frozen=True)
class DOSCurve:
    """One spin-resolved DOS-like curve.

    Attributes:
        spin: Spin channel — ``"up"`` or ``"down"``.
        energy: Energy array in Ry.
        values: DOS values in states/Ry/cell.
    """

    spin: str
    energy: np.ndarray
    values: np.ndarray

    @property
    def energy_ev(self) -> np.ndarray:
        """Energy array in eV.

        Returns:
            Energy points converted from Ry to eV.
        """
        return self.energy * RY_TO_EV

    @property
    def values_ev(self) -> np.ndarray:
        """DOS values in states/eV/cell.

        Returns:
            DOS values converted from states/Ry/cell to states/eV/cell.
        """
        return self.values / RY_TO_EV


@dataclass(frozen=True)
class DOSResult(CalculationResult):
    """Parsed result from an AkaiKKR DOS output file.

    Attributes:
        dos_components: All parsed DOS blocks — spin-up entries first, spin-down second.
        total_up: Total DOS curve for the spin-up channel, when present.
        total_down: Total DOS curve for the spin-down channel, when present.
        integrated_up: Integrated DOS curve for the spin-up channel, when present.
        integrated_down: Integrated DOS curve for the spin-down channel, when present.
        atomic_properties: Per-(type, component) electronic and magnetic properties.
    """

    dos_components: list[DOSComponent]
    total_up: DOSCurve | None = None
    total_down: DOSCurve | None = None
    integrated_up: DOSCurve | None = None
    integrated_down: DOSCurve | None = None

    @property
    def spin_up(self) -> list[DOSComponent]:
        """Return all spin-up DOS components in component-index order."""
        return [c for c in self.dos_components if c.spin == "up"]

    @property
    def spin_down(self) -> list[DOSComponent]:
        """Return all spin-down DOS components in component-index order."""
        return [c for c in self.dos_components if c.spin == "down"]

    def get_component(self, component_index: int, spin: str) -> DOSComponent | None:
        """Return one DOS component by component index and spin.

        Args:
            component_index: One-based DOS component index.
            spin: Spin channel — ``"up"`` or ``"down"``.

        Returns:
            The matching DOS component, or ``None`` if not found.
        """
        for c in self.dos_components:
            if c.component_index == component_index and c.spin == spin:
                return c
        return None

    def get(self, component_index: int, spin: str) -> DOSComponent | None:
        """Return one DOS component by component index and spin.

        Args:
            component_index: One-based DOS component index.
            spin: Spin channel — ``"up"`` or ``"down"``.

        Returns:
            The matching DOS component, or ``None`` if not found.

        Notes:
            This is a compatibility alias for ``get_component()``.
        """
        return self.get_component(component_index, spin)

    def select(
        self,
        *,
        component_index: int | None = None,
        type_name: str | None = None,
        symbol: str | None = None,
        label: str | None = None,
        spin: str | None = None,
    ) -> list[DOSComponent]:
        """Return DOS components matching the provided filters.

        Args:
            component_index: Optional one-based DOS component index filter.
            type_name: Optional AkaiKKR site-type filter.
            symbol: Optional chemical symbol filter.
            label: Optional public component-label filter.
            spin: Optional spin-channel filter.

        Returns:
            All components satisfying the provided filters.
        """
        components = self.dos_components
        if component_index is not None:
            components = [c for c in components if c.component_index == component_index]
        if type_name is not None:
            components = [c for c in components if c.type_name == type_name]
        if symbol is not None:
            components = [c for c in components if c.symbol == symbol]
        if label is not None:
            components = [c for c in components if c.label == label]
        if spin is not None:
            components = [c for c in components if c.spin == spin]
        return components

    def to_dataframe(self) -> pd.DataFrame:
        """Convert all DOS components to one pandas DataFrame.

        Returns:
            A DataFrame with one row per DOS point and columns for component
            metadata, spin, energy, orbital projections, and total DOS.
        """
        if not self.dos_components:
            return pd.DataFrame(
                columns=[
                    "component_index",
                    "type_name",
                    "symbol",
                    "label",
                    "element",
                    "spin",
                    "energy_Ry",
                    "s",
                    "p",
                    "d",
                    "f",
                    "total",
                ]
            )
        frames = []
        for comp in self.dos_components:
            n = len(comp.energy)
            frames.append(
                pd.DataFrame(
                    {
                        "component_index": comp.component_index,
                        "type_name": comp.type_name,
                        "symbol": comp.symbol,
                        "label": comp.label,
                        "element": comp.symbol,
                        "spin": comp.spin,
                        "energy_Ry": comp.energy,
                        "s": comp.s,
                        "p": comp.p,
                        "d": comp.d,
                        "f": comp.f if comp.f is not None else np.zeros(n),
                        "total": comp.total,
                    }
                )
            )
        return pd.concat(frames, ignore_index=True)
