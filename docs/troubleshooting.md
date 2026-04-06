# Troubleshooting

## Parsing errors

### `IndexError` or `ValueError` during parsing

The parser relies on fixed structural markers in the AkaiKKR output.  If you see an unexpected `IndexError` or `ValueError`, the most likely causes are:

- **Truncated file**: the calculation was interrupted before writing the footer.
  Check whether the file ends with an `OS:` / `elapsed time` block.
- **Non-standard AkaiKKR build**: some forks modify the output format slightly.
  Open an issue and attach the first 50 lines of the failing file.
- **Character encoding**: AkaiKKR sometimes writes ISO-8859-1 characters.
  The parser uses `errors="replace"` so this is handled silently, but if you
  see garbled characters in string fields, that is why.

### `dos_components` is an empty list

This means the parser found no `DOS of component N` blocks.  Verify:

1. You are passing a **DOS** output file, not an SCF output file.
2. The file completed normally (check for the `total DOS` section near the end).

---

## Spin channels

### Only spin-up components, no spin-down

This is expected for **non-magnetic** runs (`magtyp=nmag`).  Non-magnetic calculations do not produce spin-down DOS blocks.

### `dos.get_component(1, "down")` returns `None`

Either the calculation is non-magnetic (see above) or `component_index=1` does not exist.  Print `[c.component_index for c in dos.dos_components]` to inspect the available indices.

---

## Hyperfine field and charge density

### `prop.hyperfine_field` is `None`

This field is `None` when the hyperfine block is absent from the output file. Not all AkaiKKR runs write hyperfine data.  Always guard access:

```python
if prop.hyperfine_field is not None:
    print(f"Hf = {prop.hyperfine_field.total:.2f} kG")
```

The same applies to `prop.charge_density_at_nucleus`.

### `AttributeError: 'NoneType' object has no attribute 'total'`

You accessed `prop.hyperfine_field.total` (or `.charge_density_at_nucleus.total`) without checking for `None` first.  Both fields are `HyperfineField | None` and `ChargeDensityAtNucleus | None` respectively.  See the note above.

---

## DOS parsing errors

### `ParseError: DOS component N: unexpected column count M`

The parser expects each DOS block to have either 5 columns (s, p, d, total) or 6 columns (s, p, d, f, total).  If you see this error, the file may be from a non-standard AkaiKKR build that writes a different number of orbital channels. Open an issue and attach the failing block.

---

## f-orbital DOS

### `comp.f` is `None` even though the system contains f-elements

The f-orbital channel is only included when `mxl >= 3` for that site type. Check `dos.atom_types` to see the `mxl` value for each site:

```python
for t in dos.atom_types:
    print(f"{t.name}: lmxtyp={t.lmxtyp}")
```

If `mxl=2`, AkaiKKR truncates the basis at d-orbitals and no f-channel is written regardless of the element.

---

## pandas / DataFrame

### `ImportError: No module named 'pandas'`

pandas is a core dependency and should have been installed with akaitools. Reinstall the package to restore it:

```sh
pip install akaitools
# or
uv add akaitools
```

---

## Plotting

### `ImportError` when importing `akaitools.plot`

Matplotlib is a core dependency of akaitools.  If it is missing, reinstall the package:

```sh
pip install akaitools
# or with uv
uv add akaitools
```

### Energy axis looks wrong / DOS is cut off

The `ef` parameter in `plot_dos` is the **Fermi energy in Ry**, subtracted from the energy axis before plotting.  This applies to both component DOS curves and the `system_total=True` overlay. If you pass a value in eV by mistake, the shift will be roughly 13× too large.

Use the Fermi energy value from the corresponding SCF output when plotting DOS, since AkaiKKR does not write ($E_F$) explicitly in the DOS file; as a rough guide, ($E_F$) is the energy where the integrated DOS matches the electron count. If you do not want any shift, set `ef=0` to keep the raw Ry energy scale.

---

## Performance

### Parsing is slow for very large files

The parser reads the entire file into memory as a list of strings and uses regex matching throughout.  For files > 50 MB this can take a few seconds. This is a known limitation; contributions to speed up the hot paths are welcome.
