# Plotting

## Total and orbital-projected DOS

```python
from akaitools.plotting import plot_dos

fig = plot_dos(
    dos,
    ef=0.0,                       # Fermi energy in Ry, subtracted from the axis
    components=[1, 2],            # Only these component indices
    spin="up",                    # "up", "down", or None for both
    orbitals=["total", "d"],      # Any subset of s/p/d/f/total
    energy_unit="eV",             # "Ry" or "eV"
    figsize=(9, 5),
)
fig.savefig("dos.png", dpi=150)
```

## System Total DOS Overlay

```python
from akaitools.plotting import plot_dos

fig = plot_dos(
    dos,
    ef=0.0,
    orbitals=["total"],          # component totals
    system_total=True,           # add whole-system total DOS
    energy_unit="eV",
)
fig.savefig("dos_overlay.png", dpi=150)
```

To plot only the system total DOS, pass `orbitals=[]` together with `system_total=True`.

When both spin channels are present, spin-down DOS is **reflected below zero**. Non-magnetic systems naturally produce a single curve above zero.

## SCF convergence

```python
from akaitools.plotting import plot_convergence

fig = plot_convergence(scf, field="rms_error")   # or "moment", "total_energy", "total_energy_ev", "neu"
fig.savefig("convergence.png", dpi=150)
```

## Bloch spectral function (BSF)

```python
from akaitools.plotting import plot_bsf

fig = plot_bsf(
    spc,
    spin=None,                    # "up", "down", or None for both
    ef=0.0,                       # Fermi energy in Ry, subtracted from the energy axis
    energy_unit="eV",             # "Ry" or "eV"
    cmap="YlGnBu",
    vmax=None,                    # defaults to the 99.5th percentile of the intensity
)
fig.savefig("bsf.png", dpi=150)
```

When `spin=None` and both `spectral_up`/`spectral_down` carry data, the figure has two side-by-side subplots ("Spin up" / "Spin down") sharing the energy axis. High-symmetry k-points are marked with dashed vertical lines and labeled from `KMeshInfo.high_symmetry_indices`. If the relevant channel's `SpectralFunction.data` is `None` (no k-path was computed), a "No spectral data" placeholder is rendered instead of raising.

## From the command line

All three plots are also available as `akaitools plot` subcommands, so you don't need to write a script:

```sh
# DOS plot
akaitools plot dos fe.dos \
  --component 1 --component 2 \
  --spin up \
  --orbitals total,d \
  --energy-unit eV \
  --ef 0.0 \
  -o dos.png

# Only the system total DOS (empty --orbitals hides the component curves)
akaitools plot dos fe.dos --orbitals "" -o dos_total.png

# SCF convergence plot
akaitools plot scf calculation.out --field total_energy_ev -o convergence.png

# BSF plot (both spin channels, if present)
akaitools plot bsf calculation.spc \
  --base-dir /path/to/run \
  --energy-unit eV \
  --ef 0.0 \
  --cmap YlGnBu \
  -o bsf.png

# BSF plot, spin-up only, with an explicit color-scale ceiling
akaitools plot bsf calculation.spc --spin up --vmax 1.0 -o bsf_up.png
```

`akaitools plot bsf` accepts the same `--base-dir`, `--data-up`, and `--data-down` options as `akaitools spc` for locating the spectral data files. If `-o/--output` is omitted, the image is written to `<input file stem>.png` in the current directory.
