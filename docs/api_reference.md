# API Reference

## Parsing functions

::: akaitools.parse_dos

::: akaitools.parse_go

::: akaitools.parse_spc

---

## DOS result

::: akaitools.models.DOSResult

::: akaitools.models.DOSComponent

---

## SCF result

::: akaitools.models.GOResult

::: akaitools.models.GOIteration

---

## SPC result

::: akaitools.models.SPCResult

::: akaitools.models.SPCParams

::: akaitools.models.SpectralFunction

::: akaitools.models.KMeshInfo

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

---

## Plotting

::: akaitools.plot.plot_dos

::: akaitools.plot.plot_convergence

---

## Parser classes

These are used internally by `parse_dos()`, `parse_go()`, and `parse_spc()`.  You can
instantiate them directly if you need finer control over the parsing process.

::: akaitools.parsers.dos.DOSParser

::: akaitools.parsers.go.GOParser

::: akaitools.parsers.spc.SPCParser
