# CLI

!!! tip "Using uv tool"
    You can run any command below without installing `akaitools` into a project by prefixing it with `uvx`:

    ```sh
    uvx akaitools go calculation.out
    uvx akaitools dos dos.out --json
    ```

    Or install it once as a global tool (`uv tool install akaitools`) and call `akaitools` directly from any directory.

## SCF

```sh
# Summarise SCF output
akaitools go calculation.out

# JSON output (pipe-friendly)
akaitools go calculation.out --json | jq .atomic_properties
```

## DOS

```sh
# Summarise DOS output
akaitools dos dos.out

# Filter summary to component 2
akaitools dos dos.out -c 2

# JSON output
akaitools dos dos.out --json
```

## SPC

```sh
# Summarise SPC output (auto-locates *_up.spc / *_dn.spc)
akaitools spc calculation.spc

# JSON output
akaitools spc calculation.spc --json

# Override the data file search directory
akaitools spc calculation.spc --base-dir /data/run01

# Provide data files explicitly
akaitools spc calculation.spc --data-up up.spc --data-down dn.spc
```

## Plotting

```sh
# Plot DOS to fe.dos.png (defaults to the input file's stem + .png)
akaitools plot dos fe.dos -o fe_dos.png

# Plot only components 1 and 2, spin-up, total + d orbitals, in eV
akaitools plot dos fe.dos --component 1 --component 2 --spin up --orbitals total,d --energy-unit eV -o fe_dos.png

# Shift the energy axis by a Fermi energy and omit the system-total overlay
akaitools plot dos fe.dos --ef 0.6423 --no-system-total -o fe_dos.png

# Plot SCF convergence (rms_error by default)
akaitools plot scf calculation.out -o scf.png

# Plot a different convergence field
akaitools plot scf calculation.out --field total_energy_ev -o scf_energy.png

# Plot the Bloch spectral function (both spin channels, if present)
akaitools plot bsf calculation.spc --base-dir /data/run01 --energy-unit eV -o bsf.png

# Plot a single spin channel with an explicit color-scale ceiling
akaitools plot bsf calculation.spc --spin up --vmax 1.0 -o bsf_up.png
```

`akaitools plot bsf` accepts the same `--base-dir`, `--data-up`, and `--data-down` options as `akaitools spc` for locating the spectral data files.

## Sample output

```
File   : calculation.out
Date   : 2024/03/15
Lattice: fcc  a=10.95374 bohr  V=657.23 a.u.
XC     : pbe  reltyp=sra
Types  : 3   Atoms: 16   Components: 4
Converged : yes
Iterations: 47
Final moment : 3.9821 μB
Final energy : -54716.12345678 Ry

Type                 Element     Z     Charge   Spin(μB)     Hf(kG)
--------------------------------------------------------------------
X1                   X          29     8.2134     2.6543    245.123
Y1                   Y          47     6.8921    -1.2345   -123.456
Z1                   Z          78    12.1234     0.0123       N/A
```
