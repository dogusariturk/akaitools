# DataFrame export

## SCF iteration history

```python
df = scf.to_dataframe()
# columns: neu  moment  total_energy_Ry  total_energy_eV  rms_error

# Plot total energy convergence
df["total_energy_eV"].plot(title="Total energy convergence")

# Export to CSV
df.to_csv("convergence.csv", index=False)
```

## Per-component DataFrame

```python
comp = dos.get_component(1, "up")
df = comp.to_dataframe()
print(df.head())
# columns: component_index  type_name  symbol  label  element  energy_Ry  s  p  d  f  total
```

## Full dataset

```python
df = dos.to_dataframe()
# columns: component_index  type_name  symbol  label  element  spin  energy_Ry  s  p  d  f  total

# Filter to spin-up d-orbital DOS for component 1
comp_up_d = df.query("component_index == 1 and spin == 'up'")[["energy_Ry", "d"]]

# Compute total spin moment (rough integral)
import numpy as np
for idx in df["component_index"].unique():
    up   = df.query(f"component_index == {idx} and spin == 'up'")["total"].values
    down = df.query(f"component_index == {idx} and spin == 'down'")["total"].values
    dE   = df.query(f"component_index == {idx} and spin == 'up'")["energy_Ry"].diff().mean()
    moment = (up - down).sum() * dE
    print(f"Component {idx}: estimated spin moment ≈ {moment:.3f} μB")
```

## Export to CSV

```python
dos.to_dataframe().to_csv("dos_all.csv", index=False)
```
