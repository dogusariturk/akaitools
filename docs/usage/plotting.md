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

## Spin-resolved DOS

```python
from akaitools.plot import plot_dos_spin

fig = plot_dos_spin(
    dos,
    component=1,
    ef=0.0,
    orbital="d",
    energy_unit="eV",
)
fig.savefig("dos_spin.png", dpi=150)
```

The spin-down DOS is **reflected below zero** in this plot, which is the conventional representation for spin-resolved DOS.

## SCF convergence

```python
from akaitools.plot import plot_convergence

fig = plot_convergence(scf, field="rms_error")   # or "moment", "total_energy"
fig.savefig("convergence.png", dpi=150)
```
