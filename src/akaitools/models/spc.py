"""Models for AkaiKKR SPC (Bloch spectral function) results and k-paths."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

    from akaitools.models.go import GOIteration

from akaitools.models.common import CalculationResult


@dataclass(frozen=True)
class KPoint:
    """One high-symmetry k-point on a band-structure path.

    Coordinates are stored as strings to preserve fractional notation
    (e.g. ``"1/2"``, ``"3/4"``), which AkaiKKR reads directly from the
    input file.

    Attributes:
        x: First reciprocal-lattice coordinate (e.g. ``"0"``, ``"1/2"``).
        y: Second reciprocal-lattice coordinate.
        z: Third reciprocal-lattice coordinate.
        label: Optional human-readable Brillouin-zone label (e.g. ``"Γ"``,
            ``"H"``).  Stored for annotation purposes only — not written to
            the AkaiKKR input file.
    """

    x: str
    y: str
    z: str
    label: str | None = None


@dataclass(frozen=True)
class KPath:
    """A sequence of high-symmetry k-points for a band-structure calculation.

    Attributes:
        nkpts: Total number of k-points sampled along the full path.
        points: Ordered list of high-symmetry k-points defining the path.
    """

    nkpts: int
    points: list[KPoint] = field(default_factory=list)


@dataclass(frozen=True)
class SPCParams:
    """SPC-specific computational parameters from the ``***msg in spmain`` block."""

    ew: float  # Fermi energy window parameter (Ry)
    ez: float  # Imaginary part of the energy (Ry)
    preta: float  # Pre-broadening parameter
    eta: float  # Broadening parameter (Ry)
    symop_labels: tuple[str, ...]  # Symmetry operation labels (e.g. "E", "C4*3", …)
    last: int  # Number of star functions
    np: int  # Number of principal-layer repetitions
    ngpt: int  # Number of G-points in the star function set
    nrpt: int  # Number of real-space vectors
    nk: int  # Total number of k-points in the full BZ mesh
    nd: int  # Number of directions


@dataclass(frozen=True)
class KMeshInfo:
    """k-mesh and energy-mesh metadata from a spectral function data file header."""

    energy_min: float  # Lower bound of the energy mesh (Ry)
    energy_max: float  # Upper bound of the energy mesh (Ry)
    n_energy: int  # Number of energy points (rows in the data matrix)
    n_sym_points: int  # Number of high-symmetry k-point labels listed in the header
    high_symmetry_indices: dict[int, str]  # 1-based column index → Brillouin-zone label


@dataclass(frozen=True)
class SpectralFunction:
    """Bloch spectral function for one spin channel.

    Attributes:
        spin: Spin channel — ``"up"`` or ``"down"``.
        kmesh: k-mesh and energy-mesh metadata from the file header.
        data: BSF intensity matrix of shape ``(n_energy, n_kpoints)``.
            ``None`` when ``n_sym_points == 0`` (no k-path was computed).
    """

    spin: str
    kmesh: KMeshInfo
    data: np.ndarray | None


@dataclass(frozen=True)
class SPCResult(CalculationResult):
    """Parsed result from an AkaiKKR SPC output file.

    Attributes:
        spc_params: SPC-specific parameters from the ``***msg in spmain`` block.
        iteration: The single SCF iteration recorded in the file, or ``None``
            if the iteration block is absent.
        spectral_up: Spin-up Bloch spectral function, or ``None`` if the
            corresponding data file was not found.
        spectral_down: Spin-down Bloch spectral function, or ``None`` if the
            corresponding data file was not found.
    """

    spc_params: SPCParams
    iteration: GOIteration | None
    spectral_up: SpectralFunction | None = None
    spectral_down: SpectralFunction | None = None
