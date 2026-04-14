# Overview

## What is AkaiKKR?

AkaiKKR is an all-electron, relativistic, first-principles code based on the **Korringa–Kohn–Rostoker (KKR) Green's function method**.[^1] It is designed for metallic systems and disordered alloys treated via the **Coherent Potential Approximation (CPA)**.

Key capabilities of the underlying code:

- **Muffin-tin / ASA** potential, spherically symmetric within atomic spheres; the standard method in AkaiKKR
- Scalar-relativistic and fully relativistic (spin-orbit) treatments
- Spin-polarised (ferro/ferrimagnetic), paramagnetic, and non-magnetic runs
- Random alloy modelling via CPA, where each site can hold multiple chemical components with their own concentration
- Bloch spectral function (BSF) calculations for band-structure-like dispersions

## What akaitools does

AkaiKKR writes plain-text output files that contain all computed quantities. `akaitools` reads those files and converts them into structured Python objects, making the data immediately available for:

- numerical analysis with NumPy / pandas
- visualisation with Matplotlib
- export to other formats (JSON, CSV, …)

Three output types are supported:

| Output type             | Parser function | Result type |
|-------------------------|-----------------|-------------|
| SCF calculation         | `parse_go()`    | `GOResult`  |
| Density of States       | `parse_dos()`   | `DOSResult` |
| Bloch Spectral Function | `parse_spc()`   | `SPCResult` |

## Data model

=== "SCF"

    `GOResult`, returned by `parse_go()`.

    | Attribute | Type | Description |
    |-----------|------|-------------|
    | `converged` | `bool` | Whether the SCF cycle converged |
    | `iterations` | `list[GOIteration]` | Energy, moment, and RMS error per cycle |
    | `atomic_properties` | `list[AtomicProperties]` | Per-atom charge, spin/orbital moments, hyperfine field, core levels |
    | `lattice` | `LatticeInfo` | Bravais type, lattice constants, vectors, cell volume |
    | `atom_types` | `list[AtomType]` | Muffin-tin radii and CPA composition per site |
    | `positions` | `list[AtomPosition]` | Fractional coordinates |
    | `input_params` | `InputParams` | Functional, relativistic treatment, magnetic type |
    | `core_configs` | `list[CoreConfig]` | Core electron occupation per species |
    | `system_info` | `SystemInfo` | OS, hostname, CPU cores, elapsed time |

    `AtomicProperties.hyperfine_field` and `AtomicProperties.charge_density_at_nucleus` are `None` when the corresponding block is absent from the output file. Always guard access before reading fields like `.total`.

=== "DOS"

    `DOSResult`, returned by `parse_dos()`. Contains all shared fields (`lattice`, `atom_types`, `positions`, `atomic_properties`, `input_params`, `system_info`, …) and adds:

    | Attribute | Type | Description |
    |-----------|------|-------------|
    | `dos_components` | `list[DOSComponent]` | All DOS blocks, spin-up entries first and spin-down second |
    | `total_up` / `total_down` | `DOSCurve \| None` | Spin-resolved total DOS curves |
    | `integrated_up` / `integrated_down` | `DOSCurve \| None` | Spin-resolved integrated DOS curves |

    Each `DOSComponent` exposes:

    | Field | Type | Description |
    |-------|------|-------------|
    | `component_index` | `int` | CPA component number (1-based) |
    | `type_name` | `str` | AkaiKKR site-type name |
    | `symbol` | `str` | Chemical element symbol |
    | `label` | `str` | Public component label |
    | `spin` | `"up" \| "down"` | Spin channel |
    | `energy` | `ndarray` | Real-axis energy points (Ry) |
    | `s` / `p` / `d` / `f` | `ndarray` | Orbital-projected DOS (states/Ry/cell) |
    | `total` | `ndarray` | Total local DOS |

    Use `get_component(index, spin)` for exact access. Use `select(symbol=..., type_name=..., label=..., spin=...)` for metadata-based filtering.

    The number of orbital channels depends on `lmxtyp` for each site:

    | `lmxtyp` | Orbitals available |
    |----------|--------------------|
    | 2 | s, p, d, total (`f` is `None`) |
    | ≥ 3 | s, p, d, f, total |

    For **magnetic runs**, each site produces two `DOSComponent` objects (one per spin). For **non-magnetic runs** (`magtyp=nmag`), only spin-up components are present.

=== "SPC"

    `SPCResult`, returned by `parse_spc()`. Contains all shared fields (`lattice`, `atom_types`, `positions`, `atomic_properties`, `input_params`, `system_info`, …) and adds:

    | Attribute | Type | Description |
    |-----------|------|-------------|
    | `spc_params` | `SPCParams` | Energy window, broadening, and k-mesh dimensions |
    | `iteration` | `GOIteration \| None` | Single SCF iteration recorded in the SPC log |
    | `spectral_up` | `SpectralFunction \| None` | Spin-up Bloch spectral function |
    | `spectral_down` | `SpectralFunction \| None` | Spin-down Bloch spectral function |

    Each `SpectralFunction` exposes:

    | Field | Type | Description |
    |-------|------|-------------|
    | `spin` | `"up" \| "down"` | Spin channel |
    | `kmesh` | `KMeshInfo` | Energy range, number of points, high-symmetry k-point labels |
    | `data` | `ndarray \| None` | BSF intensity matrix of shape `(n_energy, n_kpoints)` |

    `data` is `None` when `n_sym_points == 0` (no k-path was computed). Always check before indexing.

## References

[^1]: H. Akai, "Fast Korringa-Kohn-Rostoker coherent potential approximation and its application to FCC Ni-Fe systems," *J. Phys.: Condens. Matter* **1**, 8045 (1989).
