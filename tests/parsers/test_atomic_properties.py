"""Tests for akaitools.parsers.atomic_properties."""

from __future__ import annotations

from akaitools.models import ChargeDensityAtNucleus, HyperfineField, ValenceCharge
from akaitools.parsers.atomic_properties import (
    parse_charge_density_at_nucleus,
    parse_core_levels,
    parse_hyperfine_field,
    parse_valence_charge,
)

_BLOCK_WITH_HYPERFINE = """
*** type-Fe  Fe  (z=  26.0)
 core charge in the muffin-tin sphere =  18.0000
 valence charge in the cell (spin up  ) =  3.0000(s)  0.5000(p)  2.5000(d)
 valence charge in the cell (spin down) =  2.5000(s)  0.4000(p)  1.5000(d)
 total charge=  26.0000  valence charge (up/down)=  6.0000  4.4000
 spin moment=   2.1686
 orbital moment=   0.0432
 core level  (spin up  )
   -512.123 Ry(1s)  -65.432 Ry(2s)  -55.123 Ry(2p)
 core level  (spin down)
   -512.098 Ry(1s)  -65.410 Ry(2s)  -55.100 Ry(2p)
 hyperfine field of Fe
   -259.216 kG  (core=  -221.111 kG  valence=  -38.105 kG  orbital=   0.000 kG)
   -18.528 kG(1s)  -55.234 kG(2s)  -147.349 kG(3s)
 charge density at the nucleus
   11820.5093  (core=  11814.6068  valence=    5.9025)
   5000.1234(1s)  3000.4567(2s)  1814.0267(3p)
"""

_BLOCK_WITHOUT_HYPERFINE = """
*** type-Ga  Ga  (z=  31.0)
 valence charge in the cell (spin up  ) =  1.0000(s)  2.0000(p)  0.0000(d)
 valence charge in the cell (spin down) =  1.0000(s)  2.0000(p)  0.0000(d)
 total charge=  31.0000  valence charge (up/down)=  3.0000  3.0000
 spin moment=   0.0000
 orbital moment=   0.0000
 core level  (spin up  )
   -400.000 Ry(1s)
 core level  (spin down)
   -400.000 Ry(1s)
"""

_BLOCK_WITH_F_ORBITAL = """
*** type-La  La  (z=  57.0)
 valence charge in the cell (spin up  ) =  0.5000(s)  1.0000(p)  0.5000(d)  0.2000(f)
 valence charge in the cell (spin down) =  0.5000(s)  1.0000(p)  0.5000(d)  0.1000(f)
 total charge=  57.0000  valence charge (up/down)=  2.2000  2.1000
 spin moment=   0.1000
 orbital moment=   0.0100
"""


def test_parse_hyperfine_field_present() -> None:
    """parse_hyperfine_field returns a HyperfineField when the block is present."""
    hf = parse_hyperfine_field(_BLOCK_WITH_HYPERFINE)
    assert isinstance(hf, HyperfineField)


def test_parse_hyperfine_field_total() -> None:
    """parse_hyperfine_field correctly reads the total field."""
    hf = parse_hyperfine_field(_BLOCK_WITH_HYPERFINE)
    assert hf is not None
    assert hf.total == -259.216


def test_parse_hyperfine_field_core_valence_orbital() -> None:
    """parse_hyperfine_field correctly reads core, valence, and orbital components."""
    hf = parse_hyperfine_field(_BLOCK_WITH_HYPERFINE)
    assert hf is not None
    assert hf.core == -221.111
    assert hf.valence == -38.105
    assert hf.orbital == 0.000


def test_parse_hyperfine_field_core_contributions() -> None:
    """parse_hyperfine_field parses per-shell core contributions."""
    hf = parse_hyperfine_field(_BLOCK_WITH_HYPERFINE)
    assert hf is not None
    assert "1s" in hf.core_contributions
    assert hf.core_contributions["1s"] == -18.528


def test_parse_hyperfine_field_absent_returns_none() -> None:
    """parse_hyperfine_field returns None when the block is absent."""
    assert parse_hyperfine_field(_BLOCK_WITHOUT_HYPERFINE) is None


def test_parse_charge_density_present() -> None:
    """parse_charge_density_at_nucleus returns ChargeDensityAtNucleus when present."""
    cd = parse_charge_density_at_nucleus(_BLOCK_WITH_HYPERFINE)
    assert isinstance(cd, ChargeDensityAtNucleus)


def test_parse_charge_density_values() -> None:
    """parse_charge_density_at_nucleus reads total, core, and valence."""
    cd = parse_charge_density_at_nucleus(_BLOCK_WITH_HYPERFINE)
    assert cd is not None
    assert cd.total == 11820.5093
    assert cd.core == 11814.6068
    assert cd.valence == 5.9025


def test_parse_charge_density_core_contributions() -> None:
    """parse_charge_density_at_nucleus parses per-shell core contributions."""
    cd = parse_charge_density_at_nucleus(_BLOCK_WITH_HYPERFINE)
    assert cd is not None
    assert "1s" in cd.core_contributions


def test_parse_charge_density_absent_returns_none() -> None:
    """parse_charge_density_at_nucleus returns None when block is absent."""
    assert parse_charge_density_at_nucleus(_BLOCK_WITHOUT_HYPERFINE) is None


def test_parse_valence_charge_spin_up() -> None:
    """parse_valence_charge reads s/p/d for spin up."""
    vc = parse_valence_charge(_BLOCK_WITH_HYPERFINE, "spin up")
    assert isinstance(vc, ValenceCharge)
    assert vc.s == 3.0
    assert vc.p == 0.5
    assert vc.d == 2.5


def test_parse_valence_charge_no_f_when_lmxtyp2() -> None:
    """parse_valence_charge sets f=None when the f channel is absent."""
    vc = parse_valence_charge(_BLOCK_WITH_HYPERFINE, "spin up")
    assert vc.f is None


def test_parse_valence_charge_with_f() -> None:
    """parse_valence_charge reads f when the f channel is present."""
    vc = parse_valence_charge(_BLOCK_WITH_F_ORBITAL, "spin up")
    assert vc.f == 0.2


def test_parse_valence_charge_missing_returns_zeros() -> None:
    """parse_valence_charge returns a zero-filled ValenceCharge when the line is absent."""
    vc = parse_valence_charge("no valence data here", "spin up")
    assert vc.s == 0.0
    assert vc.p == 0.0
    assert vc.d == 0.0


def test_parse_core_levels_spin_up() -> None:
    """parse_core_levels reads binding energies for spin up."""
    levels = parse_core_levels(_BLOCK_WITH_HYPERFINE, "spin up")
    assert "1s" in levels
    assert levels["1s"] == -512.123


def test_parse_core_levels_spin_down() -> None:
    """parse_core_levels reads binding energies for spin down."""
    levels = parse_core_levels(_BLOCK_WITH_HYPERFINE, "spin down")
    assert "1s" in levels
    assert levels["1s"] == -512.098


def test_parse_core_levels_missing_returns_empty() -> None:
    """parse_core_levels returns {} when the section is absent."""
    assert parse_core_levels("no core data", "spin up") == {}
