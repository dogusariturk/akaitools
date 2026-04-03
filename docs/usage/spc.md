# SPC output

```python
from akaitools import parse_spc

spc = parse_spc("calculation.spc")
```

The `*_up.spc` and `*_dn.spc` data files are located automatically next to the log file
(using `input_params.file` as the stem).  Override either path explicitly when needed:

```python
spc = parse_spc(
    "calculation.spc",
    data_up="/data/up.spc",
    data_down="/data/dn.spc",
)
```

## k-mesh and energy range

```python
bsf = spc.spectral_up
if bsf is not None:
    km = bsf.kmesh
    print(f"Energy range : {km.energy_min:.4f} – {km.energy_max:.4f} Ry")
    print(f"Energy points: {km.n_energy}")
    print(f"k-path labels: {km.high_symmetry_indices}")  # e.g. {1: 'G', 25: 'H', 50: 'N'}
```

## BSF intensity matrix

`SpectralFunction.data` is a NumPy array of shape `(n_energy, n_kpoints)`.
`None` when `n_sym_points == 0` (no k-path was computed).

```python
import numpy as np

if bsf is not None and bsf.data is not None:
    print(f"Shape: {bsf.data.shape}")  # (n_energy, n_kpoints)

    # Energy axis in eV (1 Ry = 13.6057 eV)
    energy_Ry = np.linspace(bsf.kmesh.energy_min, bsf.kmesh.energy_max, bsf.kmesh.n_energy)
    energy_eV = energy_Ry * 13.6057

    # Intensity at the Fermi level (energy closest to 0 Ry)
    ef_idx = int(np.argmin(np.abs(energy_Ry)))
    print(f"BSF row at E_F: {bsf.data[ef_idx, :]}")
```

## Plotting the spectral function

There is no dedicated `plot_spc` helper yet, but the intensity matrix is a plain NumPy
array so Matplotlib's `imshow` or `pcolormesh` work directly:

```python
import matplotlib.pyplot as plt
import numpy as np

bsf = spc.spectral_up
if bsf is not None and bsf.data is not None:
    km = bsf.kmesh
    energy = np.linspace(km.energy_min, km.energy_max, km.n_energy) * 13.6057  # eV
    kpoints = np.arange(bsf.data.shape[1])

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.pcolormesh(kpoints, energy, bsf.data, cmap="hot_r", shading="auto")
    ax.axhline(0, color="cyan", lw=0.8, ls="--", label="$E_F$")

    # High-symmetry k-point labels
    for k_idx, label in km.high_symmetry_indices.items():
        ax.axvline(k_idx - 1, color="white", lw=0.5, ls="--")
        ax.text(k_idx - 1, energy[-1], label, ha="center", va="bottom", color="white")

    ax.set_xlabel("k-point index")
    ax.set_ylabel("Energy (eV)")
    ax.set_title(f"Bloch Spectral Function ({bsf.spin})")
    fig.tight_layout()
    fig.savefig("bsf.png", dpi=150)
```

## SPC parameters

```python
sp = spc.spc_params
print(f"Energy window : {sp.ew:.4f} Ry")
print(f"Broadening eta: {sp.eta:.4f} Ry")
print(f"k-points (BZ) : {sp.nk}")
print(f"Directions    : {sp.nd}")

for prop in spc.atomic_properties:
    print(f"  {prop.element}: m_spin={prop.spin_moment:.4f} μB")
```
