# Shared data models

## Result base class

`GOResult`, `DOSResult`, and `SPCResult` all inherit from `CalculationResult`, which provides the shared header fields (lattice, atom types, system info, …) plus `to_dict()`/`to_json()` serialization.

::: akaitools.models.CalculationResult

---

## Shared data models

::: akaitools.models.AtomicProperties

::: akaitools.models.ValenceCharge

::: akaitools.models.HyperfineField

::: akaitools.models.ChargeDensityAtNucleus

::: akaitools.models.LatticeInfo

::: akaitools.models.AtomType

::: akaitools.models.AtomicComponent

::: akaitools.models.AtomPosition

::: akaitools.models.CoreConfig

::: akaitools.models.EnergyPoint

::: akaitools.models.InputParams

::: akaitools.models.SystemInfo
