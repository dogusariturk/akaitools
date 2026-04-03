# akaitools

[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg)](https://spdx.org/licenses/GPL-3.0-or-later.html)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Platforms](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey)](https://github.com/dogusariturk/akaitools)
[![Tests](https://github.com/dogusariturk/akaitools/actions/workflows/tests.yml/badge.svg)](https://github.com/dogusariturk/akaitools/actions/workflows/tests.yml)
[![Lint](https://github.com/dogusariturk/akaitools/actions/workflows/lint.yml/badge.svg)](https://github.com/dogusariturk/akaitools/actions/workflows/lint.yml)

**akaitools** parses output files from [AkaiKKR](http://kkr.issp.u-tokyo.ac.jp/), a Korringa–Kohn–Rostoker (KKR) Green's function code for electronic structure calculations. It turns raw text output into structured, fully typed Python objects without any manual text wrangling.

---

## Key features

- Parse **SCF**, **DOS**, and **BSF** output files with a single function call (`parse_go`, `parse_dos`, `parse_spc`)
- Spin-resolved DOS with direct access via `spin_up`, `spin_down`, `get_component()`, and `select()`
- Bloch Spectral Function intensity matrix with k-path high-symmetry labels
- Export any result to a pandas DataFrame for downstream analysis
- Built-in Matplotlib plotting for DOS and SCF convergence
- Command-line interface for quick summaries and JSON export
- Fully typed: all models are standard Python `dataclass` objects

---

## Quickstart

=== "SCF"

    ```python
    from akaitools import parse_go

    scf = parse_go("calculation.out")

    print(f"Converged   : {scf.converged}")
    print(f"Iterations  : {len(scf.iterations)}")
    print(f"Total energy: {scf.iterations[-1].total_energy:.8f} Ry")
    print(f"Moment      : {scf.iterations[-1].moment:.4f} μB")

    for prop in scf.atomic_properties:
        print(f"  {prop.element:<4s}  charge={prop.total_charge:.3f}  m={prop.spin_moment:.4f} μB")
    ```

=== "DOS"

    ```python
    from akaitools import parse_dos

    dos = parse_dos("dos.out")

    # Spin-resolved access
    for comp in dos.spin_up:
        print(f"Component {comp.component_index} [{comp.label}] ↑: {len(comp.energy)} points")

    # Direct lookup by component index and spin
    fe_up = dos.get_component(1, "up")
    print(f"Energy range: {fe_up.energy[0]:.3f} – {fe_up.energy[-1]:.3f} Ry")
    print(f"d-DOS max   : {fe_up.d.max():.4f} states/Ry/cell")

    # Export to pandas
    df = dos.to_dataframe()
    print(df.head())
    ```

=== "SPC"

    ```python
    from akaitools import parse_spc

    # *_up.spc / *_dn.spc are located automatically next to the log file
    spc = parse_spc("calculation.spc")

    if spc.spectral_up is not None and spc.spectral_up.data is not None:
        bsf = spc.spectral_up
        print(f"BSF shape: {bsf.data.shape}")   # (n_energy, n_kpoints)
        print(f"k-labels : {bsf.kmesh.high_symmetry_indices}")
    ```

=== "Plotting"

    ```python
    from akaitools import parse_dos, parse_go
    from akaitools.plot import plot_convergence, plot_dos, plot_dos_spin

    scf = parse_go("calculation.out")
    dos = parse_dos("dos.out")

    # SCF convergence
    plot_convergence(scf, field="rms_error").savefig("convergence.png", dpi=150)

    # Total + d-orbital DOS, energy in eV
    plot_dos(dos, ef=0.0, orbitals=["total", "d"], energy_unit="eV").savefig("dos.png", dpi=150)

    # Spin-resolved DOS (spin-down reflected below zero)
    plot_dos_spin(dos, component=1, orbital="d", ef=0.0).savefig("dos_spin.png", dpi=150)
    ```

=== "CLI"

    ```sh
    # Summarise an SCF output
    akaitools go  calculation.out

    # Summarise a DOS output, filtered to component 1
    akaitools dos dos.out -c 1

    # Summarise a BSF output
    akaitools spc calculation.spc

    # JSON output (pipe-friendly)
    akaitools go calculation.out --json | jq .atomic_properties
    ```
