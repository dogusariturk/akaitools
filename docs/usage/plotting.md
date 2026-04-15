# Plotting

## Total and orbital-projected DOS

```python
from akaitools.plot import plot_dos

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
from akaitools.plot import plot_dos

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
from akaitools.plot import plot_convergence

fig = plot_convergence(scf, field="rms_error")   # or "moment", "total_energy", "total_energy_ev", "neu"
fig.savefig("convergence.png", dpi=150)
```
