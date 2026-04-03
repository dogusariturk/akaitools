"""Tests for akaitools.models."""

from __future__ import annotations

import numpy as np
import pytest

from akaitools.models import (
    AtomicComponent,
    AtomType,
    ChargeDensityAtNucleus,
    DOSComponent,
    DOSResult,
    HyperfineField,
    InputParams,
    LatticeInfo,
    SystemInfo,
    ValenceCharge,
)


def test_valence_charge_no_f() -> None:
    """ValenceCharge.f defaults to None."""
    vc = ValenceCharge(s=1.0, p=2.0, d=3.0)
    assert vc.f is None


def test_valence_charge_with_f() -> None:
    """ValenceCharge.f is set when provided."""
    vc = ValenceCharge(s=1.0, p=2.0, d=3.0, f=0.5)
    assert vc.f == pytest.approx(0.5)


def test_hyperfine_field_stores_values() -> None:
    """HyperfineField stores all four field components."""
    hf = HyperfineField(total=-100.0, core=-90.0, valence=-8.0, orbital=-2.0, core_contributions={"1s": -50.0})
    assert hf.total == pytest.approx(-100.0)
    assert hf.core == pytest.approx(-90.0)
    assert hf.valence == pytest.approx(-8.0)
    assert hf.orbital == pytest.approx(-2.0)
    assert hf.core_contributions["1s"] == pytest.approx(-50.0)


def test_charge_density_at_nucleus_stores_values() -> None:
    """ChargeDensityAtNucleus stores total, core, and valence."""
    cd = ChargeDensityAtNucleus(total=1000.0, core=990.0, valence=10.0, core_contributions={"1s": 500.0})
    assert cd.total == pytest.approx(1000.0)
    assert cd.core == pytest.approx(990.0)
    assert cd.valence == pytest.approx(10.0)


def _make_dos_component(index: int = 1, spin: str = "up", n: int = 5) -> DOSComponent:
    energy = np.linspace(-0.5, 0.5, n)
    dos = np.ones(n) * 0.1
    return DOSComponent(
        component_index=index,
        type_name="Fe",
        symbol="Fe",
        label="Fe",
        spin=spin,
        energy=energy,
        s=dos,
        p=dos,
        d=dos,
        total=dos,
    )


def test_dos_component_element_property() -> None:
    """DOSComponent.element returns the chemical symbol."""
    comp = _make_dos_component()
    assert comp.element == "Fe"


def test_dos_component_f_is_none_by_default() -> None:
    """DOSComponent.f is None when not supplied."""
    comp = _make_dos_component()
    assert comp.f is None


def test_dos_component_to_dataframe_columns() -> None:
    """DOSComponent.to_dataframe() returns expected column names."""
    comp = _make_dos_component()
    df = comp.to_dataframe()
    for col in ("component_index", "type_name", "symbol", "label", "element", "energy_Ry", "s", "p", "d", "f", "total"):
        assert col in df.columns


def test_dos_component_to_dataframe_row_count() -> None:
    """to_dataframe() produces one row per energy point."""
    comp = _make_dos_component(n=10)
    assert len(comp.to_dataframe()) == 10


def _make_dos_result() -> DOSResult:
    up1 = _make_dos_component(index=1, spin="up")
    up2 = _make_dos_component(index=2, spin="up")
    down1 = _make_dos_component(index=1, spin="down")
    down2 = _make_dos_component(index=2, spin="down")

    return DOSResult(
        date="2025-01-01",
        time="00:00:00",
        meshr=400,
        mse=5,
        ng=21,
        mxl=3,
        input_params=InputParams(
            go="go",
            file="f",
            brvtyp="fcc",
            a=6.0,
            c_over_a=1.0,
            b_over_a=1.0,
            alpha=90.0,
            beta=90.0,
            gamma=90.0,
            edelt=0.001,
            ewidth=1.0,
            reltyp="sra",
            sdftyp="pbe",
            magtyp="mag",
            record="2nd",
            outtyp="stdout",
            bzqlty=5,
            maxitr="100",
            pmix=0.1,
            mixtyp="simple",
            ntyp=1,
            natm=1,
            ncmpx=2,
        ),
        energy_mesh=[],
        lattice=LatticeInfo(
            bravais="fcc",
            a=6.0,
            c_over_a=1.0,
            b_over_a=1.0,
            alpha=90.0,
            beta=90.0,
            gamma=90.0,
            volume=100.0,
            volume_filling=0.7,
            primitive_vectors=((0.5, 0.5, 0.0), (0.5, 0.0, 0.5), (0.0, 0.5, 0.5)),
            reciprocal_vectors=((1.0, 1.0, -1.0), (1.0, -1.0, 1.0), (-1.0, 1.0, 1.0)),
        ),
        atom_types=[AtomType(name="Fe", rmt=0.4, field=0.0, lmxtyp=2, components=[AtomicComponent(anclr=26.0, conc=1.0)])],
        positions=[],
        core_configs=[],
        atomic_properties=[],
        system_info=SystemInfo(os="Linux", host="host", machine="x86_64", num_cores=4, elapsed_time=1.0, num_threads=4),
        dos_components=[up1, up2, down1, down2],
    )


def test_dos_result_spin_up() -> None:
    """DOSResult.spin_up returns only up-spin components."""
    r = _make_dos_result()
    up = r.spin_up
    assert len(up) == 2
    assert all(c.spin == "up" for c in up)


def test_dos_result_spin_down() -> None:
    """DOSResult.spin_down returns only down-spin components."""
    r = _make_dos_result()
    down = r.spin_down
    assert len(down) == 2
    assert all(c.spin == "down" for c in down)


def test_dos_result_get_component_found() -> None:
    """get_component() returns the matching component."""
    r = _make_dos_result()
    comp = r.get_component(2, "down")
    assert comp is not None
    assert comp.component_index == 2
    assert comp.spin == "down"


def test_dos_result_get_component_missing() -> None:
    """get_component() returns None when the component does not exist."""
    r = _make_dos_result()
    assert r.get_component(99, "up") is None


def test_dos_result_get_alias() -> None:
    """.get() is an alias for get_component()."""
    r = _make_dos_result()
    assert r.get(1, "up") is r.get_component(1, "up")


def test_dos_result_select_by_spin() -> None:
    """select(spin=...) filters to one spin channel."""
    r = _make_dos_result()
    result = r.select(spin="up")
    assert len(result) == 2
    assert all(c.spin == "up" for c in result)


def test_dos_result_select_by_symbol() -> None:
    """select(symbol=...) filters to matching chemical symbol."""
    r = _make_dos_result()
    result = r.select(symbol="Fe")
    assert len(result) == 4


def test_dos_result_select_by_index_and_spin() -> None:
    """select() can filter by both component_index and spin."""
    r = _make_dos_result()
    result = r.select(component_index=1, spin="down")
    assert len(result) == 1
    assert result[0].component_index == 1


def test_dos_result_to_dataframe_all_components() -> None:
    """to_dataframe() concatenates all components."""
    r = _make_dos_result()
    df = r.to_dataframe()
    # 4 components × 5 energy points each
    assert len(df) == 4 * 5
    assert "spin" in df.columns


def test_dos_result_to_dataframe_empty() -> None:
    """to_dataframe() on an empty result returns empty DataFrame with correct columns."""
    r = _make_dos_result()
    r.dos_components = []
    df = r.to_dataframe()
    assert len(df) == 0
    assert "energy_Ry" in df.columns


def test_dos_result_select_by_type_name() -> None:
    """select(type_name=...) filters to components with matching type_name."""
    r = _make_dos_result()
    result = r.select(type_name="Fe")
    assert len(result) == 4  # all components have type_name "Fe"


def test_dos_result_select_by_type_name_no_match() -> None:
    """select(type_name=...) returns empty list when no component matches."""
    r = _make_dos_result()
    result = r.select(type_name="Ni")
    assert result == []


def test_dos_result_select_by_label() -> None:
    """select(label=...) filters to components with matching label."""
    r = _make_dos_result()
    result = r.select(label="Fe")
    assert len(result) == 4  # all components have label "Fe"


def test_dos_result_select_by_label_no_match() -> None:
    """select(label=...) returns empty list when no component matches."""
    r = _make_dos_result()
    result = r.select(label="NiFe:Fe")
    assert result == []
