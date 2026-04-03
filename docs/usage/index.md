# Usage

akaitools turns AkaiKKR plain-text output into structured Python objects with a single function call:

```python
from akaitools import parse_go, parse_dos, parse_spc

scf = parse_go("calculation.out")
dos = parse_dos("dos.out")
spc = parse_spc("calculation.spc")
```

Select a topic below to get started.

<div class="grid cards" markdown>

-   :material-sine-wave: **SCF output**

    ---

    Parse convergence history, crystal structure, and per-atom electronic and magnetic properties.

    [:octicons-arrow-right-24: SCF](scf.md)

-   :material-chart-bell-curve: **DOS output**

    ---

    Access spin-resolved density of states components by index, element, or site type. Export to pandas.

    [:octicons-arrow-right-24: DOS](dos.md)

-   :material-map-legend: **SPC output**

    ---

    Read Bloch Spectral Function data and plot band-structure-like dispersions with k-path labels.

    [:octicons-arrow-right-24: SPC](spc.md)

-   :material-chart-line: **Plotting**

    ---

    Ready-made Matplotlib figures for DOS, spin-resolved DOS, and SCF convergence.

    [:octicons-arrow-right-24: Plotting](plotting.md)

-   :material-table: **DataFrame export**

    ---

    Convert any DOS result to a pandas DataFrame for filtering, integration, and CSV export.

    [:octicons-arrow-right-24: DataFrame export](dataframe.md)

-   :material-console: **CLI**

    ---

    Quick summaries and JSON output from the command line, with no Python required.

    [:octicons-arrow-right-24: CLI](cli.md)

</div>
