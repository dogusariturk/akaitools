# Installation & Quick Start

## Requirements

- Python **3.10** or newer
- NumPy ≥ 1.26
- pandas ≥ 2.0
- Matplotlib ≥ 3.8
- Typer ≥ 0.12

## Install

=== "uv (recommended)"

    ```sh
    uv add akaitools
    ```

=== "pip"

    ```sh
    pip install akaitools
    ```

=== "From source"

    ```sh
    git clone https://github.com/dogusariturk/akaitools.git
    cd akaitools
    pip install .
    ```

## As a standalone CLI tool

If you only need the `akaitools` command-line interface and don't want to add it to a project,
install it as an isolated tool with [uv tool](https://docs.astral.sh/uv/concepts/tools/):

```sh
uv tool install akaitools
```

The `akaitools` command is then available globally without activating any virtual environment.
Upgrade or remove it at any time:

```sh
uv tool upgrade akaitools
uv tool uninstall akaitools
```

**One-shot execution:** to run a single command without a permanent install, use `uvx`
(short for `uv tool run`):

```sh
uvx akaitools go calculation.out
uvx akaitools dos dos.out -c 1 --json
```

## Extra dependencies

### Documentation

To build these docs locally:

```sh
pip install "akaitools[docs]"
mkdocs serve
```

### Development

```sh
uv sync --group dev
uv run pytest
```

---

## Quick start

### Parse an SCF output

```python
from akaitools import parse_go

scf = parse_go("calculation.out")

print(f"Converged: {scf.converged}")
print(f"Iterations: {len(scf.iterations)}")
print(f"Total energy: {scf.iterations[-1].total_energy:.8f} Ry")
print(f"Magnetic moment: {scf.iterations[-1].moment:.4f} μB")
print()
for prop in scf.atomic_properties:
    print(f"{prop.element:>4s}  charge={prop.total_charge:.3f}  m={prop.spin_moment:.3f} μB")
```

### Parse a DOS output

```python
from akaitools import parse_dos

dos = parse_dos("dos.out")

# Iterate over spin-up components directly
for comp in dos.spin_up:
    print(f"Component {comp.component_index} [{comp.label}] ↑: {len(comp.energy)} energy points")

# Get a specific component by index and spin
comp_up = dos.get_component(1, "up")
if comp_up is not None:
    print(f"Energy range: {comp_up.energy[0]:.3f} – {comp_up.energy[-1]:.3f} Ry")
    print(f"Max d-DOS: {comp_up.d.max():.4f} states/Ry/cell")

# Or select semantically
comp_up = dos.select(symbol="X", spin="up")
print(f"X up-spin components: {[comp.component_index for comp in comp_up]}")
```

### Plot DOS

```python
from akaitools.plot import plot_dos, plot_dos_spin

# Total DOS for all components, Fermi level shifted to 0
fig = plot_dos(dos, ef=0.0, orbitals=["total", "d"], energy_unit="eV")
fig.savefig("dos.png", dpi=150)

# Spin-resolved plot (spin-down reflected below zero)
fig = plot_dos_spin(dos, component=1, orbital="d", ef=0.0)
fig.savefig("dos_spin.png", dpi=150)
```

### Command-line interface

```sh
# Summarise an SCF output
akaitools go calculation.out

# Print JSON
akaitools go calculation.out --json

# Summarise a DOS output, filtered to component 1
akaitools dos dos.out -c 1
```
