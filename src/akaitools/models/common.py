"""Shared structural building blocks for parsed AkaiKKR results."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from akaitools.utils import to_serializable

if TYPE_CHECKING:
    from akaitools.models.atomic_properties import AtomicProperties


@dataclass(frozen=True)
class EnergyPoint:
    """One point in the complex energy mesh."""

    real: float
    imag: float


@dataclass(frozen=True)
class AtomicComponent:
    """One chemical component within a mixed (CPA) site."""

    anclr: float  # Atomic number
    conc: float  # Concentration (0-1)


@dataclass(frozen=True)
class AtomType:
    """One site type, potentially a CPA alloy mixture."""

    name: str
    rmt: float  # Muffin-tin radius (in units of a)
    field: float  # External field (in Ry)
    lmxtyp: int  # Maximum angular momentum quantum number
    components: list[AtomicComponent] = field(default_factory=list)


@dataclass(frozen=True)
class AtomPosition:
    """Fractional position of an atom in the unit cell."""

    x: float
    y: float
    z: float
    atom_type: str


@dataclass(frozen=True)
class LatticeInfo:
    """Bravais lattice and cell geometry."""

    bravais: str
    a: float  # Lattice constant in bohr
    c_over_a: float
    b_over_a: float
    alpha: float  # Degrees
    beta: float
    gamma: float
    volume: float  # Unit cell volume in a.u.
    volume_filling: float  # Muffin-tin filling fraction (0-1)
    primitive_vectors: tuple[tuple[float, float, float], ...]  # In units of a
    reciprocal_vectors: tuple[tuple[float, float, float], ...]  # In units of 2π/a


@dataclass(frozen=True)
class CoreConfig:
    """Electronic core configuration for one atomic species."""

    z: int  # Atomic number
    states: tuple[str, ...]  # State labels ("1s", "2s", "2p", …)
    up: tuple[int, ...]  # Spin-up occupation per state
    down: tuple[int, ...]  # Spin-down occupation per state


@dataclass(frozen=True)
class InputParams:
    """Parameters from the 'data read in' header block."""

    go: str
    file: str
    brvtyp: str
    a: float
    c_over_a: float
    b_over_a: float
    alpha: float
    beta: float
    gamma: float
    edelt: float
    ewidth: float
    reltyp: str
    sdftyp: str
    magtyp: str
    record: str
    outtyp: str
    bzqlty: int
    maxitr: str  # May be "***" (unlimited)
    pmix: float
    mixtyp: str
    ntyp: int
    natm: int
    ncmpx: int


@dataclass(frozen=True)
class SystemInfo:
    """Computational environment and timing information."""

    os: str
    host: str
    machine: str
    num_cores: int
    elapsed_time: float  # Seconds
    num_threads: int


@dataclass(frozen=True)
class CalculationResult:
    """Shared metadata parsed from an AkaiKKR output file."""

    date: str
    time: str
    meshr: int
    mse: int
    ng: int
    mxl: int
    input_params: InputParams
    energy_mesh: list[EnergyPoint]
    lattice: LatticeInfo
    atom_types: list[AtomType]
    positions: list[AtomPosition]
    core_configs: list[CoreConfig]
    atomic_properties: list[AtomicProperties]
    system_info: SystemInfo

    def to_dict(self) -> dict:
        """Convert this result to a JSON-serializable dictionary.

        Numpy arrays embedded in fields are converted to plain lists
        so the result can be passed to ``json.dumps()`` directly.

        Returns:
            A nested dictionary representation of this result.
        """
        return to_serializable(self)

    def to_json(self, path: Path | str | None = None, **kwargs: Any) -> str | None:
        """Serialize this result to JSON.

        Args:
            path: If given, write the JSON to this file path and return ``None``.
                If omitted, return the JSON as a string instead.
            **kwargs: Additional keyword arguments forwarded to ``json.dumps()``.

        Returns:
            A JSON string representation of this result, or ``None`` if ``path``
            was given.
        """
        text = json.dumps(self.to_dict(), **kwargs)
        if path is None:
            return text
        Path(path).write_text(text, encoding="utf-8")
        return None
