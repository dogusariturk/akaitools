# FAQ

## General

### Which AkaiKKR versions are supported?

akaitools is tested against output files from the version distributed at
[kkr.issp.u-tokyo.ac.jp](http://kkr.issp.u-tokyo.ac.jp/).  The output format
has been stable for many years, so older files should parse correctly.  If you
encounter a format mismatch, please open an issue on GitHub.

### Which output file types are supported?

| AkaiKKR run type | Parser function | Result type |
|------------------|-----------------|-------------|
| `go=scf`         | `parse_go()`    | `GOResult`  |
| `go=dos`         | `parse_dos()`   | `DOSResult` |
| `go=spc`         | `parse_spc()`   | `SPCResult` |

All three parsers share common logic for sections that appear in every output
file (lattice, atom types, atomic properties, system info) and each additionally
extracts the section unique to its run type.

### What units does the parser use?

All quantities are returned in the **native AkaiKKR units** unless the plotting
utilities are used with `energy_unit="eV"`:

| Quantity             | Unit               |
|----------------------|--------------------|
| Energy (DOS, SCF)    | Rydberg (Ry)       |
| Lattice constant `a` | Bohr               |
| Cell volume          | Bohr³ (a.u.)       |
| Magnetic moment      | Bohr magneton (μB) |
| Hyperfine field      | Kilogauss (kG)     |
| DOS                  | states / Ry / cell |

---

## DOS

### What is a "CPA component"?

In CPA calculations, each crystallographic site can be occupied by a mixture of
chemical species.  Each species on a site is called a **component**, identified
by its `component_index`.  For a pure element, there is only one component per
site.  For a 50/50 binary alloy on one sublattice, there are two.

### How do I access the DOS for a specific element or site?

Use exact lookup for one known component, or metadata-based selection when the
same element appears on multiple inequivalent sites:

```python
# Exact access
comp = dos.get_component(1, "up")

# All up-spin components for element X
x_up = dos.select(symbol="X", spin="up")

# One inequivalent site by AkaiKKR type name
x_site = dos.select(type_name="X_1", spin="up")

# CPA-resolved label for a mixed site
mixed_x = dos.select(label="XY_2:X", spin="up")
```

`component_index` is the canonical identifier. `symbol`, `type_name`, and
`label` are convenience filters.

### Why does `spin_down` return an empty list?

The calculation was likely non-magnetic (`magtyp=nmag`).  In non-magnetic runs
AkaiKKR does not compute separate spin channels; only `spin_up` will contain
data.

### How do I compute the total DOS (sum over all sites)?

```python
import numpy as np

energy = dos.spin_up[0].energy           # common energy grid
total_up   = sum(c.total for c in dos.spin_up)
total_down = sum(c.total for c in dos.spin_down)

import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot(energy, total_up,    label="spin up")
ax.plot(energy, -total_down, label="spin down")
ax.axhline(0, color="k", lw=0.6)
ax.legend()
```

---

## SCF

### Where is the Fermi energy?

AkaiKKR does not write the Fermi energy explicitly in the output file.  You can
infer it from the energy axis of the DOS file (the zero of the energy mesh is
typically set near the Fermi level) or compute it from the integrated DOS.

### How do I extract the total magnetic moment?

```python
scf = parse_go("calculation.out")
m_total = scf.iterations[-1].moment      # μB, from the last SCF iteration
```

For the site-decomposed moments:

```python
for prop in scf.atomic_properties:
    print(f"{prop.element}: {prop.spin_moment:.4f} μB (spin)  "
          f"{prop.orbital_moment:.4f} μB (orbital)")
```

---

## SPC

### Why is `spectral_up` or `spectral_down` `None`?

`parse_spc()` auto-discovers the `*_up.spc` / `*_dn.spc` data files next to the
log file.  If a data file cannot be found, the corresponding attribute is `None`
rather than raising an error.  Check the file paths and, if needed, pass them
explicitly:

```python
spc = parse_spc("calculation.spc", data_up="fe_up.spc", data_down="fe_dn.spc")
```

### Why is `SpectralFunction.data` `None` even though the file was found?

The header of the data file records `n_sym_points`.  When `n_sym_points == 0`
no k-path was computed for that spin channel and no data rows are present.
Always check before indexing:

```python
if spc.spectral_up is not None and spc.spectral_up.data is not None:
    print(spc.spectral_up.data.shape)
```

### What are the units of the BSF intensity?

The Bloch Spectral Function intensity stored in `SpectralFunction.data` is in
**states / Ry / cell** (same units as the DOS).  The energy axis runs from
`kmesh.energy_min` to `kmesh.energy_max` in **Ry** with `kmesh.n_energy` points.

---

## Output and export

### How do I export results to JSON?

```python
import json, dataclasses, numpy as np

def _serialise(obj):
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(type(obj))

with open("dos.json", "w") as f:
    json.dump(dos, f, default=_serialise, indent=2)
```

Or use the CLI:

```sh
akaitools dos dos.out --json > dos.json
```

### How do I convert the DOS to a CSV?

```python
dos.to_dataframe().to_csv("dos.csv", index=False)
```
