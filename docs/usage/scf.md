# SCF output

```python
from akaitools import parse_go

scf = parse_go("calculation.out")
```

## Convergence history

```python
from akaitools.plot import plot_convergence

# Iterate over SCF cycles
for it in scf.iterations[-5:]:      # last 5 iterations
    print(f"  iter {it.iteration:3d}  E={it.total_energy:.8f} Ry  "
          f"m={it.moment:.4f} μB  log10(rms)={it.rms_error:.2f}")

# Plot convergence
fig = plot_convergence(scf, field="rms_error")
fig.savefig("convergence.png")
```

## Crystal structure

```python
lat = scf.lattice
print(f"Bravais: {lat.bravais}")
print(f"a = {lat.a:.5f} bohr  ({lat.a * 0.529177:.5f} Å)")
print(f"Volume = {lat.volume:.3f} a.u.")
print(f"Muffin-tin filling = {lat.volume_filling * 100:.1f} %")

for pos in scf.positions:
    print(f"  {pos.atom_type:>10s}  ({pos.x:.4f}, {pos.y:.4f}, {pos.z:.4f})")
```

## Per-atom properties

```python
for prop in scf.atomic_properties:
    hf = f"{prop.hyperfine_field.total:.2f} kG" if prop.hyperfine_field is not None else "N/A"
    print(
        f"{prop.element} ({prop.type_name}): "
        f"charge={prop.total_charge:.3f}  "
        f"m_spin={prop.spin_moment:.4f} μB  "
        f"m_orb={prop.orbital_moment:.4f} μB  "
        f"Hf={hf}"
    )
```

!!! note
    `prop.hyperfine_field` and `prop.charge_density_at_nucleus` are `None` when the corresponding block is absent from the output (e.g. non-relativistic or non-magnetic runs that omit the hyperfine section). Always guard access with a `None` check before reading fields like `.total`.
