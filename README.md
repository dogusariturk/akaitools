<div align="center">

# akaitools

**A Python library for parsing and analyzing [AkaiKKR](http://kkr.issp.u-tokyo.ac.jp/) electronic structure output files**

[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg)](https://spdx.org/licenses/GPL-3.0-or-later.html)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Platforms](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey)](https://github.com/dogusariturk/akaitools)

[![Tests](https://github.com/dogusariturk/akaitools/actions/workflows/tests.yml/badge.svg)](https://github.com/dogusariturk/akaitools/actions/workflows/tests.yml)
[![Lint](https://github.com/dogusariturk/akaitools/actions/workflows/lint.yml/badge.svg)](https://github.com/dogusariturk/akaitools/actions/workflows/lint.yml)

[Documentation](https://dogusariturk.github.io/akaitools) · [Report a Bug](https://github.com/dogusariturk/akaitools/issues/new?labels=bug) · [Request a Feature](https://github.com/dogusariturk/akaitools/issues/new?labels=enhancement)

</div>

---

`akaitools` parses output files from **AkaiKKR**, a Korringa–Kohn–Rostoker (KKR) Green's function code for electronic structure calculations. It turns raw text output into structured Python objects ready for analysis and visualization.

**What it parses:**

- SCF convergence history (energy, magnetic moment, RMS error per iteration)
- Per-atom electronic and magnetic properties (charges, spin/orbital moments, core levels, hyperfine fields)
- Crystal structure (Bravais type, lattice constants, vectors, atomic positions)
- Density of States per-component, per-orbital (*s*, *p*, *d*, *f*, total), spin-resolved
- Bloch Spectral Function (BSF) spin-resolved spectral weight on a k-path with high-symmetry labels

---

## Installation

```sh
# Recommended using uv
uv add akaitools

# Alternative using pip
pip install akaitools

# From source
pip install git+https://github.com/dogusariturk/akaitools.git
```

**CLI-only usage with uv tool:** install `akaitools` as a standalone tool available globally, without adding it to a project:

```sh
uv tool install akaitools
```

Or run a one-off command without any installation using `uvx`:

```sh
uvx akaitools go  calculation.out
uvx akaitools dos dos.out --json
```

---

## Quick Start

### SCF output

Use `parse_go` to parse a self-consistent field output file. The result contains the full convergence history, per-atom electronic and magnetic properties, and crystal structure information.

```python
from akaitools import parse_go

scf = parse_go("calculation.out")

print(f"Converged : {scf.converged}")
print(f"Energy    : {scf.iterations[-1].total_energy:.8f} Ry")
print(f"Moment    : {scf.iterations[-1].moment:.4f} μB")

for prop in scf.atomic_properties:
    print(f"  {prop.element:<4s}  charge={prop.total_charge:.3f}  m={prop.spin_moment:.4f} μB")
```

### DOS output

Use `parse_dos` to parse a density of states output file. Components can be accessed by index and spin with `get_component`, or filtered by element, site type, or label with `select`.

```python
from akaitools import parse_dos

dos = parse_dos("dos.out")

# Exact lookup by component index and spin
fe_up = dos.get_component(1, "up")
print(f"Energy range : {fe_up.energy[0]:.3f} – {fe_up.energy[-1]:.3f} Ry")
print(f"d-DOS max    : {fe_up.d.max():.4f} states/Ry/cell")

# Filter by metadata
x_components = dos.select(symbol="X", spin="up")
```

### SPC output

Use `parse_spc` to parse a Bloch Spectral Function output. The `*_up.spc` and `*_dn.spc` data files are located automatically next to the log file, or can be provided explicitly via `data_up` and `data_down`.

```python
from akaitools import parse_spc

spc = parse_spc("calculation.spc")

if spc.spectral_up is not None:
    bsf = spc.spectral_up
    print(f"k-points     : {bsf.data.shape[1]}")
    print(f"Energy points: {bsf.kmesh.n_energy}")
    print(f"High-symmetry: {bsf.kmesh.high_symmetry_indices}")  # e.g. {1: 'G', 25: 'H'}
```

### Plotting

`akaitools.plot` provides ready-made Matplotlib figures for the most common visualizations. All functions return a `Figure` object for further customization before saving.

```python
from akaitools.plot import plot_dos, plot_dos_spin, plot_convergence

plot_dos(dos, ef=0.0, orbitals=["total", "d"]).savefig("dos.png")
plot_dos_spin(dos, component=1, orbital="d").savefig("dos_spin.png")
plot_convergence(scf, field="rms_error").savefig("convergence.png")
```

### CLI

The `akaitools` command provides quick summaries of output files without writing any Python. Use `--json` for machine-readable output.

```sh
akaitools go  calculation.out         # summarize SCF output
akaitools go  calculation.out --json  # output as JSON
akaitools dos dos.out -c 1            # DOS summary for component 1
```

---

## Data Model

### SCF output

| Attribute           | Type                     | Description                                                         |
|---------------------|--------------------------|---------------------------------------------------------------------|
| `converged`         | `bool`                   | Whether the SCF cycle converged                                     |
| `iterations`        | `list[GOIteration]`      | Energy, moment, and RMS error per cycle                             |
| `atomic_properties` | `list[AtomicProperties]` | Per-atom charge, spin/orbital moments, hyperfine field, core levels |
| `lattice`           | `LatticeInfo`            | Bravais type, lattice constants, vectors, cell volume               |
| `atom_types`        | `list[AtomType]`         | Muffin-tin radii and CPA composition per site                       |
| `positions`         | `list[AtomPosition]`     | Fractional coordinates                                              |
| `input_params`      | `InputParams`            | Functional, relativistic treatment, magnetic type                   |
| `system_info`       | `SystemInfo`             | OS, hostname, CPU cores, elapsed time                               |

### DOS output

Inherits all SCF fields, and adds:

| Attribute                          | Type                 | Description                                          |
|------------------------------------|----------------------|------------------------------------------------------|
| `dos_components`                   | `list[DOSComponent]` | *s*, *p*, *d*, *f*, total DOS per component per spin |
| `total_up`, `total_down`           | `DOSCurve \| None`   | Spin-resolved total DOS curves                       |
| `integrated_up`, `integrated_down` | `DOSCurve \| None`   | Spin-resolved integrated DOS curves                  |

Each `DOSComponent` exposes `component_index`, `type_name`, `symbol`, `label`, `spin`, `energy`, `s`, `p`, `d`, `f`, and `total`.

### SPC output

Inherits all SCF fields, and adds:

| Attribute       | Type                       | Description                                                           |
|-----------------|----------------------------|-----------------------------------------------------------------------|
| `spc_params`    | `SPCParams`                | Energy window, broadening, symmetry operations, and k-mesh dimensions |
| `iteration`     | `GOIteration \| None`      | Single SCF iteration recorded in the SPC log                          |
| `spectral_up`   | `SpectralFunction \| None` | Spin-up Bloch spectral function                                       |
| `spectral_down` | `SpectralFunction \| None` | Spin-down Bloch spectral function                                     |

Each `SpectralFunction` exposes `spin`, `data` (the BSF intensity matrix), and `kmesh` (`KMeshInfo` with energy range, grid size, and high-symmetry k-point labels).

---

## License

Released under the [GPL-3.0-or-later](./LICENSE) license.
