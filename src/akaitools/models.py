"""Data models for AkaiKKR output files."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class EnergyPoint:
    """One point in the complex energy mesh."""

    real: float
    imag: float


@dataclass
class AtomicComponent:
    """One chemical component within a mixed (CPA) site."""

    anclr: float  # Atomic number
    conc: float  # Concentration (0-1)


@dataclass
class AtomType:
    """One site type, potentially a CPA alloy mixture."""

    name: str
    rmt: float  # Muffin-tin radius (in units of a)
    field: float  # External field (in Ry)
    lmxtyp: int  # Maximum angular momentum quantum number
    components: list[AtomicComponent] = field(default_factory=list)


@dataclass
class AtomPosition:
    """Fractional position of an atom in the unit cell."""

    x: float
    y: float
    z: float
    atom_type: str


@dataclass
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


@dataclass
class CoreConfig:
    """Electronic core configuration for one atomic species."""

    z: int  # Atomic number
    states: tuple[str, ...]  # State labels ("1s", "2s", "2p", …)
    up: tuple[int, ...]  # Spin-up occupation per state
    down: tuple[int, ...]  # Spin-down occupation per state


@dataclass
class GOIteration:
    """Data from one self-consistent field iteration."""

    iteration: int
    neu: float  # Number of electrons (charge neutrality measure)
    moment: float  # Total magnetic moment (μB)
    total_energy: float  # Total energy (Ry)
    rms_error: float  # Log10 of RMS error


@dataclass
class ValenceCharge:
    """Orbital-resolved valence charge for one spin channel."""

    s: float
    p: float
    d: float
    f: float | None = None  # Only present when lmxtyp >= 3


@dataclass
class HyperfineField:
    """Hyperfine magnetic field at the nucleus."""

    total: float  # kG
    core: float  # kG
    valence: float  # kG
    orbital: float  # kG
    core_contributions: dict[str, float]  # {"1s": value_kG, "2s": value_kG, …}


@dataclass
class ChargeDensityAtNucleus:
    """Charge density at the nuclear site."""

    total: float
    core: float
    valence: float
    core_contributions: dict[str, float]  # {"1s": value, "2s": value, …}


@dataclass
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


@dataclass
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


@dataclass
class SystemInfo:
    """Computational environment and timing information."""

    os: str
    host: str
    machine: str
    num_cores: int
    elapsed_time: float  # Seconds
    num_threads: int


@dataclass
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


@dataclass
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
        s: s-orbital projected DOS, shape ``(n_points,)``.
        p: p-orbital projected DOS.
        d: d-orbital projected DOS.
        total: Total local DOS (sum of all orbital channels).
        f: f-orbital projected DOS; ``None`` when ``lmxtyp < 3``.
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
                "s": self.s,
                "p": self.p,
                "d": self.d,
                "f": self.f if self.f is not None else np.zeros(len(self.energy)),
                "total": self.total,
            }
        )


@dataclass
class DOSCurve:
    """One spin-resolved DOS-like curve."""

    spin: str
    energy: np.ndarray
    values: np.ndarray


@dataclass
class GOResult(CalculationResult):
    """Parsed result from an AkaiKKR GO output file."""

    iterations: list[GOIteration]
    converged: bool


@dataclass
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


@dataclass
class KMeshInfo:
    """k-mesh and energy-mesh metadata from a spectral function data file header."""

    energy_min: float  # Lower bound of the energy mesh (Ry)
    energy_max: float  # Upper bound of the energy mesh (Ry)
    n_energy: int  # Number of energy points (rows in the data matrix)
    n_sym_points: int  # Number of high-symmetry k-point labels listed in the header
    high_symmetry_indices: dict[int, str]  # 1-based column index → Brillouin-zone label


@dataclass
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


@dataclass
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


@dataclass
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
