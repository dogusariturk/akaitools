"""Per-site electronic and magnetic property models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValenceCharge:
    """Orbital-resolved valence charge for one spin channel."""

    s: float
    p: float
    d: float
    f: float | None = None  # Only present when lmxtyp >= 3


@dataclass(frozen=True)
class HyperfineField:
    """Hyperfine magnetic field at the nucleus."""

    total: float  # kG
    core: float  # kG
    valence: float  # kG
    orbital: float  # kG
    core_contributions: dict[str, float]  # {"1s": value_kG, "2s": value_kG, …}


@dataclass(frozen=True)
class ChargeDensityAtNucleus:
    """Charge density at the nuclear site."""

    total: float
    core: float
    valence: float
    core_contributions: dict[str, float]  # {"1s": value, "2s": value, …}


@dataclass(frozen=True)
class AtomicProperties:
    """Complete electronic properties for one (type, component) pair."""

    type_name: str
    element: str
    z: float
    core_charge_muffin_tin: float
    valence_up: ValenceCharge
    valence_down: ValenceCharge
    total_charge: float
    valence_charge_up: float
    valence_charge_down: float
    spin_moment: float  # μB
    orbital_moment: float  # μB
    core_levels_up: dict[str, float]  # {"1s": energy_Ry, …}
    core_levels_down: dict[str, float]
    hyperfine_field: HyperfineField | None
    charge_density_at_nucleus: ChargeDensityAtNucleus | None
