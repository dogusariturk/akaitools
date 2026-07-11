# Input file generation

`akaitools` can generate AkaiKKR input files from scratch or by reconstructing them from any previously parsed result.

```python
from akaitools import InputFile
```

---

## Build from scratch

Construct an `InputFile` by specifying the crystal structure and calculation parameters directly. Required fields are `mode`, `data_file`, `bravais`, `a`,`atom_types`, and `positions`; every other parameter has a sensible default.

```python
from akaitools import InputFile
from akaitools.models import AtomicComponent, AtomPosition, AtomType

fe = InputFile(
    mode="go",
    data_file="data/fe",
    bravais="bcc",
    a=5.27,
    atom_types=[
        AtomType(
            name="Fe",
            rmt=0.0,        # 0 → AkaiKKR assigns the radius automatically
            field=0.0,
            lmxtyp=2,
            components=[AtomicComponent(anclr=26.0, conc=1.0)],
        )
    ],
    positions=[AtomPosition(x=0.0, y=0.0, z=0.0, atom_type="Fe")],
    edelt=0.001,
    ewidth=1.0,
    reltyp="nrl",
    sdftyp="mjwasa",
    bzqlty=8,
    maxitr=100,
    pmix=0.035,
)

print(fe.to_string())   # render to string
fe.write("fe.in")       # write to disk
```

### CPA alloys

For CPA (Coherent Potential Approximation) alloys, define multiple components on a single site type. Concentrations must be fractions and sum to 1.0.

```python
from akaitools import InputFile
from akaitools.models import AtomicComponent, AtomPosition, AtomType

nife = InputFile(
    mode="go",
    data_file="data/nife",
    bravais="fcc",
    a=6.55,
    atom_types=[
        AtomType(
            name="NiFe",
            rmt=0.0,
            field=0.0,
            lmxtyp=2,
            components=[
                AtomicComponent(anclr=28.0, conc=0.5),   # 50 % Ni
                AtomicComponent(anclr=26.0, conc=0.5),   # 50 % Fe
            ],
        )
    ],
    positions=[AtomPosition(x=0.0, y=0.0, z=0.0, atom_type="NiFe")],
)
nife.write("nife.in")
```

### Multi-site structures

```python
gaas = InputFile(
    mode="go",
    data_file="data/gaas",
    bravais="fcc",
    a=10.684,
    reltyp="sra",
    sdftyp="mjw",
    magtyp="mag",
    bzqlty=4,
    atom_types=[
        AtomType("Ga",  rmt=0.0, field=0.0, lmxtyp=2, components=[AtomicComponent(31.0, 1.0)]),
        AtomType("As",  rmt=0.0, field=0.0, lmxtyp=2, components=[AtomicComponent(33.0, 1.0)]),
        AtomType("Vc1", rmt=0.0, field=0.0, lmxtyp=0, components=[AtomicComponent(0.0,  1.0)]),
        AtomType("Vc2", rmt=0.0, field=0.0, lmxtyp=0, components=[AtomicComponent(0.0,  1.0)]),
    ],
    positions=[
        AtomPosition(0.00, 0.00, 0.00, "Ga"),
        AtomPosition(0.25, 0.25, 0.25, "As"),
        AtomPosition(0.50, 0.50, 0.50, "Vc1"),
        AtomPosition(0.75, 0.75, 0.75, "Vc2"),
    ],
)
```

---

## Reconstruct from a parsed result

`InputFile.from_result()` re-creates an input file from any `GOResult`, `DOSResult`, or `SPCResult`. This is useful for tweaking parameters and re-running an existing calculation.

```python
from akaitools import InputFile, parse_go

scf = parse_go("calculation.out")

# Reconstruct with the same parameters
inp = InputFile.from_result(scf)
inp.write("rerun.in")
```

### Change the calculation mode

Pass `mode` to override the mode recorded in the original file:

```python
# Reconstruct as a DOS input from an SCF result
inp = InputFile.from_result(scf, mode="dos")
inp.bzqlty = 12           # increase k-mesh quality
inp.write("dos.in")

# Reconstruct as an SPC input
inp = InputFile.from_result(scf, mode="spc")
inp.write("spc.in")
```

### Muffin-tin radii

`from_result` preserves the computed muffin-tin radii from the parsed result by default. Pass `reset_rmt=True` to zero them out so AkaiKKR recomputes them automatically on the next run:

```python
inp = InputFile.from_result(scf, reset_rmt=True)
```

---

## Band structure (SPC k-path)

For Bloch Spectral Function calculations, attach a `KPath` to an SPC-mode input. Coordinates support fractional notation (`"1/2"`, `"3/4"`) directly.

```python
from akaitools import InputFile, KPath, KPoint, parse_go

scf = parse_go("calculation.out")

kpath = KPath(
    nkpts=300,
    points=[
        KPoint("0",   "0",   "0",   label="Γ"),
        KPoint("0",   "1",   "0",   label="H"),
        KPoint("1/2", "1/2", "0",   label="N"),
        KPoint("1/2", "1/2", "1/2", label="P"),
        KPoint("0",   "0",   "0",   label="Γ"),
        KPoint("1/2", "1/2", "0",   label="N"),
    ],
)

inp = InputFile.from_result(scf, mode="spc", kpath=kpath)
inp.write("fe_spc.in")
```

!!! note
    `KPoint.label` is for documentation only — it is not written to the AkaiKKR input file. High-symmetry labels appear in the `.spc` output after the calculation runs.

---

## Parse an existing input file

`InputFile.from_file()` and `InputFile.from_string()` parse a hand-written or previously rendered `.in` file back into an `InputFile`, the inverse of `to_string()`/`write()`.

```python
from akaitools import InputFile

inp = InputFile.from_file("fe.in")
inp.bzqlty = 12          # tweak a parameter
inp.write("fe_rerun.in")

# Or parse text already in memory
inp = InputFile.from_string(open("fe.in").read())
```

!!! note
    `to_string()` never writes `KPoint.label`, so labels cannot be recovered when parsing an SPC input with a k-path — every parsed `KPoint.label` is `None`. Coordinates round-trip exactly.

`from_file()`/`from_string()` follow AkaiKKR's own free-format reading rules, not just the layout `to_string()` happens to write, so hand-written files parse too:

- A leading title comment is optional — AkaiKKR itself has no concept of one.
- `bravais="aux"` or `"prv"` is supported: the three primitive vectors are read in place of `c/a`, `b/a`, and the lattice angles, and stored on `InputFile.primitive_vectors`.
- `bzqlty` accepts either an integer mesh count or one of AkaiKKR's quality letter codes (`"t"`, `"l"`, `"m"`, `"h"`, `"u"`).
- `magtyp` is a free string (e.g. `"kick3"`), not limited to `"mag"`/`"nmag"`.
- `pmix` and a directly-appended mixing-type suffix (e.g. `"0.02br"`) are split into `pmix` and `mixtyp`.
- Atomic-position coordinates may carry a redundant direction letter (e.g. `"0.5a"`); it is stripped when parsing.

---

## Render and inspect

```python
# Render to a string without writing to disk
text = inp.to_string()
print(text)

# Write to a specific path
inp.write("calculations/fe/go.in")
```

---

## Error handling

`InputFile` validates its fields on construction and raises `InputValidationError` with a `field` attribute that names the offending parameter:

```python
from akaitools.errors import InputValidationError

try:
    bad = InputFile(mode="xyz", ...)
except InputValidationError as exc:
    print(exc.field)    # "mode"
    print(exc)          # "mode: must be one of ['dos', 'go', 'spc'], got 'xyz'"
```

Common causes:

| `field`                      | Cause                                                       |
|------------------------------|-------------------------------------------------------------|
| `"mode"`                     | Not one of `"go"`, `"dos"`, `"spc"`                         |
| `"atom_types"`               | Empty list                                                  |
| `"positions"`                | Empty list                                                  |
| `"atom_types[X].components"` | Empty component list, or concentrations don't sum to 1.0    |
| `"positions[N].atom_type"`   | References a type name not defined in `atom_types`          |
| `"kpath"`                    | `kpath` is set but `mode` is not `"spc"`                    |
| `"primitive_vectors"`        | Missing when `bravais` is `"aux"`/`"prv"`, or set otherwise |
