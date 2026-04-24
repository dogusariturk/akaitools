<div align="center">

<img width="200" height="200" alt="akaitools-logo" src="https://github.com/user-attachments/assets/9553bd80-5bab-4722-9eff-410121e5dee2" />

# akaitools

[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg)](https://spdx.org/licenses/GPL-3.0-or-later.html)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platforms](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey)

[![Tests](https://github.com/dogusariturk/akaitools/actions/workflows/tests.yml/badge.svg)](https://github.com/dogusariturk/akaitools/actions/workflows/tests.yml)
[![Lint](https://github.com/dogusariturk/akaitools/actions/workflows/lint.yml/badge.svg)](https://github.com/dogusariturk/akaitools/actions/workflows/lint.yml)

`akaitools` parses output files from [AkaiKKR](http://kkr.issp.u-tokyo.ac.jp/), a Korringa-Kohn-Rostoker (KKR) Green's function code for electronic structure calculations. It turns raw text output into structured, fully typed Python objects and can generate new AkaiKKR input files from scratch or from parsed results.

<p>
  <a href="https://github.com/dogusariturk/akaitools/issues/new?labels=bug">Report a Bug</a> |
  <a href="https://github.com/dogusariturk/akaitools/issues/new?labels=enhancement">Request a Feature</a> |
  <a href="https://dogusariturk.github.io/akaitools">Documentation</a>
</p>

</div>

---

## Key features

- Parse **SCF**, **DOS**, and **SPC/BSF** outputs with `parse_go()`, `parse_dos()`, and `parse_spc()`
- Access spin-resolved DOS through `spin_up`, `spin_down`, `get_component()`, and `select()`
- Read Bloch spectral function matrices with automatic spectral-data discovery and high-symmetry k-point labels
- Work with frozen dataclass models backed by NumPy arrays, with eV conversion helpers on energy-bearing fields
- Export DOS and SCF iteration data to pandas with `.to_dataframe()`
- Generate Matplotlib figures for DOS and SCF convergence with `akaitools.plot`
- Inspect files from the terminal with `akaitools go|dos|spc`
- Build AkaiKKR inputs programmatically with `InputFile`, including CPA alloys, multi-site structures, and SPC `KPath` / `KPoint` definitions

---

## Installation

```sh
# Recommended
uv add akaitools

# pip
pip install akaitools

# Latest from GitHub
pip install git+https://github.com/dogusariturk/akaitools.git
```

For CLI-only use: install `akaitools` as a standalone tool available globally, without adding it to a project:

```sh
uv tool install akaitools
```

Or run one-off commands without installing:

```sh
uvx akaitools go calculation.out
uvx akaitools dos dos.out --json
```

---

## Quickstart

### SCF output

Use `parse_go` to parse a self-consistent field output file. The result contains the full convergence history, per-atom electronic and magnetic properties, and crystal structure information.

```python
from akaitools import parse_go

scf = parse_go("calculation.out")

print(f"Converged   : {scf.converged}")
print(f"Iterations  : {len(scf.iterations)}")
print(f"Total energy: {scf.iterations[-1].total_energy:.8f} Ry")
print(f"Moment      : {scf.iterations[-1].moment:.4f} uB")

df = scf.to_dataframe()  # columns: neu, moment, total_energy_Ry, total_energy_eV, rms_error
```

### DOS output

Use `parse_dos` to parse a density of states output file. Components can be accessed by index and spin with `get_component`, or filtered by element, site type, or label with `select`.

```python
from akaitools import parse_dos

dos = parse_dos("dos.out")

for comp in dos.spin_up:
    print(f"Component {comp.component_index} [{comp.label}] up: {len(comp.energy)} points")

fe_up = dos.get_component(1, "up")
print(f"Energy range: {fe_up.energy[0]:.3f} to {fe_up.energy[-1]:.3f} Ry")
print(f"d-DOS max   : {fe_up.d.max():.4f} states/Ry/cell")

x_up = dos.select(symbol="X", spin="up")
df = dos.to_dataframe()
```

### SPC output

Use `parse_spc` to parse a Bloch Spectral Function output. The `*_up.spc` and `*_dn.spc` data files are located automatically next to the log file, or can be provided explicitly via `data_up` and `data_down`.

```python
from akaitools import parse_spc

spc = parse_spc("calculation.spc")

if spc.spectral_up is not None and spc.spectral_up.data is not None:
    bsf = spc.spectral_up
    print(f"BSF shape: {bsf.data.shape}")
    print(f"k-labels : {bsf.kmesh.high_symmetry_indices}")
```

`parse_spc()` auto-locates `*_up.spc` and `*_dn.spc` next to the log file. Use `base_dir`, `data_up`, or `data_down` to override the discovery logic when needed.

### Plotting

`akaitools.plot` provides ready-made Matplotlib figures for the most common visualizations. All functions return a `Figure` object for further customization before saving.

```python
from akaitools import parse_dos, parse_go
from akaitools.plot import plot_convergence, plot_dos

scf = parse_go("calculation.out")
dos = parse_dos("dos.out")

plot_convergence(scf, field="rms_error").savefig("convergence.png")
plot_dos(dos, orbitals=["total", "d"], energy_unit="eV").savefig("dos.png")
plot_dos(dos, orbitals=["total"]).savefig("dos_overlay.png")
```

### CLI

The `akaitools` command provides quick summaries of output files without writing any Python. Use `--json` for machine-readable output.

```sh
akaitools go calculation.out                          # summarize SCF output
akaitools go calculation.out --json                   # output as JSON
akaitools dos dos.out -c 1                            # DOS summary for component 1
akaitools spc calculation.spc --base-dir /path/to/run # SPC summary
```

### Input generation

Use `InputFile` to write a new AkaiKKR input file from scratch. All parameters have sensible defaults; only `mode`, `data_file`, `bravais`, `a`, `atom_types`, and `positions` are required.

```python
from akaitools import InputFile, KPath, KPoint, parse_go
from akaitools.models import AtomicComponent, AtomPosition, AtomType

fe = InputFile(
    mode="go",
    data_file="data/fe",
    bravais="bcc",
    a=5.27,
    atom_types=[
        AtomType(
            name="Fe",
            rmt=0.0,
            field=0.0,
            lmxtyp=2,
            components=[AtomicComponent(anclr=26.0, conc=1.0)],
        )
    ],
    positions=[AtomPosition(x=0.0, y=0.0, z=0.0, atom_type="Fe")],
)
fe.write("fe.in")

scf = parse_go("calculation.out")
InputFile.from_result(scf, mode="dos").write("dos.in")

kpath = KPath(
    nkpts=300,
    points=[
        KPoint("0", "0", "0", label="G"),
        KPoint("0", "1", "0", label="H"),
        KPoint("1/2", "1/2", "0", label="N"),
    ],
)
InputFile.from_result(scf, mode="spc", kpath=kpath).write("spc.in")
```

---

## License

This project is licensed under the GNU GPLv3 License. See [LICENSE](https://github.com/dogusariturk/akaitools/blob/main/LICENSE).

---

## Citation

We are currently preparing a preprint for publication.
