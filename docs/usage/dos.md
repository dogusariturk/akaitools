# DOS output

```python
from akaitools import parse_dos

dos = parse_dos("dos.out")
```

## Iterating over components

```python
# All components, spin-up first and spin-down second
for comp in dos.dos_components:
    print(f"  comp {comp.component_index} [{comp.label}] ({comp.spin}): "
          f"{len(comp.energy)} points, d-max={comp.d.max():.4f}")
```

## Spin-resolved access

Use the `spin_up` and `spin_down` properties to avoid filtering manually:

```python
# All majority-spin components
for comp in dos.spin_up:
    print(f"comp {comp.component_index} ↑  E=[{comp.energy[0]:.3f}, {comp.energy[-1]:.3f}] Ry")

# All minority-spin components
import numpy as np
for comp in dos.spin_down:
    fermi_idx = int(np.argmin(np.abs(comp.energy)))  # energy point nearest E_F = 0
    print(f"comp {comp.component_index} ↓  d-DOS at Ef ≈ {comp.d[fermi_idx]:.4f}")
```

## Direct lookup by index and spin

```python
# Retrieve a single component without list comprehensions
comp = dos.get_component(1, "up")
if comp is not None:
    print(f"Energy range: {comp.energy[0]:.3f} – {comp.energy[-1]:.3f} Ry")
    print(f"d-DOS max   : {comp.d.max():.4f} states/Ry/cell")
```

!!! tip
    `get_component()` returns `None` (not an error) when the requested
    component or spin channel is absent. Always check the return value before
    using it.

## Selection by metadata

```python
# All up-spin DOS components for element X
x_up = dos.select(symbol="X", spin="up")

# One inequivalent site by AkaiKKR type name
x_site = dos.select(type_name="X_1", spin="up")

# CPA-resolved label for mixed sites
mixed_x = dos.select(label="XY_2:X", spin="up")
```

Use `component_index` for exact access. Use `type_name`, `symbol`, or `label`
when you want site-aware filtering.

## f-orbital DOS

```python
comp = dos.get_component(1, "up")
if comp is not None:
    if comp.f is not None:
        print("f-orbital DOS present")
        print(f"f-DOS max: {comp.f.max():.4f}")
    else:
        print("No f-orbital DOS (lmxtyp < 3)")
```
