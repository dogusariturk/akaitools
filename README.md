<div align="center">

# akaitools

[![License: GPL--3.0--or--later](https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg)](https://spdx.org/licenses/GPL-3.0-or-later.html)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platforms](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey)
[![Tests](https://github.com/dogusariturk/akaitools/actions/workflows/tests.yml/badge.svg)](https://github.com/dogusariturk/akaitools/actions/workflows/tests.yml)
[![Lint](https://github.com/dogusariturk/akaitools/actions/workflows/lint.yml/badge.svg)](https://github.com/dogusariturk/akaitools/actions/workflows/lint.yml)

`akaitools` is a Python library for parsing output files produced by **AkaiKKR**, a Korringa–Kohn–Rostoker (KKR) Green's function code for electronic structure calculations. It extracts SCF convergence data, per-atom electronic and magnetic properties, crystal structure information, and Density of States (DOS) components into structured Python objects ready for analysis and visualization.

<p>
  <a href="https://github.com/dogusariturk/akaitools/issues/new?labels=bug">Report a Bug</a> |
  <a href="https://github.com/dogusariturk/akaitools/issues/new?labels=enhancement">Request a Feature</a>
</p>

</div>

---

## Installation

```sh
# Recommended — using uv
uv add akaitools

# Alternative — using pip
pip install akaitools

# From source
pip install git+https://github.com/dogusariturk/akaitools.git
```

Core install includes the CLI, plotting utilities, and pandas support. Optional
extras currently cover documentation tooling only.

```sh
pip install .[docs]           # Documentation build dependencies
uv sync --group dev           # Development tools from dependency groups
```

---

## Quick Start

```python
from akaitools import parse_go, parse_dos

# Parse an SCF output file
result = parse_go("calculation.out")

print(f"Converged: {result.converged}")
print(f"Total energy: {result.iterations[-1].total_energy} Ry")
print(f"Magnetic moment: {result.iterations[-1].moment} μB")

for prop in result.atomic_properties:
    print(f"{prop.element}: spin moment = {prop.spin_moment} μB")

# Parse a DOS output file
dos = parse_dos("dos.out")

for comp in dos.dos_components:
    print(f"Component {comp.component_index} [{comp.label}] ({comp.spin}): "
          f"{len(comp.energy)} energy points")

# Exact lookup by component index and spin
fe_up = dos.get_component(1, "up")
print(fe_up.type_name, fe_up.symbol, fe_up.label)

# Semantic selection by metadata
all_ga_up = dos.select(symbol="Ga", spin="up")
```

### Plotting

```python
from akaitools.plot import plot_dos, plot_dos_spin, plot_convergence

# Total and d-projected DOS
fig = plot_dos(dos, ef=0.0, orbitals=["total", "d"])
fig.savefig("dos.png")

# Spin-resolved DOS for two components
fig = plot_dos_spin(dos, up_component=1, down_component=1, orbital="total")
fig.savefig("dos_spin.png")

# SCF convergence history
fig = plot_convergence(result, field="rms_error")
fig.savefig("convergence.png")
```

### Command-Line Interface

```sh
# Summarize an SCF output
akaitools go calculation.out

# Output as JSON
akaitools go calculation.out --json

# Summarize a DOS output, filtered to one component
akaitools dos dos.out -c 1
```

---

## Parsed Data

### SCF Output (`GOResult`)

| Attribute | Type | Description |
|-----------|------|-------------|
| `converged` | `bool` | Whether the SCF cycle converged |
| `iterations` | `list[GOIteration]` | Per-iteration energy, moment, and RMS error |
| `atomic_properties` | `list[AtomicProperties]` | Per-atom charges, moments, core levels; `hyperfine_field` and `charge_density_at_nucleus` are `None` when absent from the output |
| `lattice` | `LatticeInfo` | Bravais type, lattice constants, vectors, cell volume |
| `atom_types` | `list[AtomType]` | Muffin-tin radii, CPA components, external fields |
| `positions` | `list[AtomPosition]` | Fractional coordinates |
| `input_params` | `InputParams` | Functional, relativistic treatment, magnetic type, composition |
| `system_info` | `SystemInfo` | OS, hostname, CPU cores, elapsed time |

### DOS Output (`DOSResult`)

Shares all structural fields with `GOResult`, and adds:

| Attribute | Type | Description |
|-----------|------|-------------|
| `dos_components` | `list[DOSComponent]` | Per-component, per-spin DOS arrays (s, p, d, f, total) |
| `total_up`, `total_down` | `DOSCurve \| None` | Spin-resolved total DOS curves |
| `integrated_up`, `integrated_down` | `DOSCurve \| None` | Spin-resolved integrated DOS curves |

Each `DOSComponent` exposes `component_index`, `type_name`, `symbol`, `label`, `spin`, `energy`, `s`, `p`, `d`, `f`, and `total`. Use `get_component(component_index, spin)` for exact lookup and `select(...)` for metadata-based filtering.

---

## References

- H. Akai, "Fast Korringa-Kohn-Rostoker coherent potential approximation and its application to FCC Ni-Fe systems," *Journal of Physics: Condensed Matter*, vol. 1, no. 43, pp. 8045–8064, 1989.
- P. H. Dederichs *et al.*, "Ab initio calculations of the electronic structure of impurities and alloys of ferromagnetic transition metals," *Journal of Magnetism and Magnetic Materials*, vol. 45, no. 1, pp. 15–22, 1984.

---

## License

This project is licensed under the GPL-3.0-or-later license. See the [LICENSE](./LICENSE) file for details.
