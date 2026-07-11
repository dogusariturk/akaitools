"""Tests for akaitools.models."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest

from akaitools import parse_dos, parse_go, parse_spc
from akaitools.models import (
    AtomicComponent,
    AtomType,
    ChargeDensityAtNucleus,
    DOSComponent,
    DOSCurve,
    DOSResult,
    GOIteration,
    GOResult,
    HyperfineField,
    InputParams,
    LatticeInfo,
    SystemInfo,
    ValenceCharge,
)
from akaitools.utils import RY_TO_EV


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
    for col in (
        "component_index",
        "type_name",
        "symbol",
        "label",
        "element",
        "energy_Ry",
        "energy_eV",
        "s",
        "p",
        "d",
        "f",
        "total",
    ):
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
    r = dataclasses.replace(_make_dos_result(), dos_components=[])
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


class TestDOSComponentEvProperties:
    """Tests for DOSComponent eV-unit properties."""

    def test_energy_ev(self) -> None:
        """energy_ev returns energy array scaled by RY_TO_EV."""
        comp = _make_dos_component()
        np.testing.assert_allclose(comp.energy_ev, comp.energy * RY_TO_EV)

    def test_s_ev(self) -> None:
        """s_ev returns s DOS divided by RY_TO_EV."""
        comp = _make_dos_component()
        np.testing.assert_allclose(comp.s_ev, comp.s / RY_TO_EV)

    def test_p_ev(self) -> None:
        """p_ev returns p DOS divided by RY_TO_EV."""
        comp = _make_dos_component()
        np.testing.assert_allclose(comp.p_ev, comp.p / RY_TO_EV)

    def test_d_ev(self) -> None:
        """d_ev returns d DOS divided by RY_TO_EV."""
        comp = _make_dos_component()
        np.testing.assert_allclose(comp.d_ev, comp.d / RY_TO_EV)

    def test_total_ev(self) -> None:
        """total_ev returns total DOS divided by RY_TO_EV."""
        comp = _make_dos_component()
        np.testing.assert_allclose(comp.total_ev, comp.total / RY_TO_EV)

    def test_f_ev_none_when_f_is_none(self) -> None:
        """f_ev is None when f is not set."""
        comp = _make_dos_component()
        assert comp.f is None
        assert comp.f_ev is None

    def test_f_ev_converts_when_f_is_set(self) -> None:
        """f_ev returns f DOS divided by RY_TO_EV when f is present."""
        base = _make_dos_component()
        comp = dataclasses.replace(base, f=np.ones(len(base.energy)) * 0.2)
        assert comp.f_ev is not None
        assert comp.f is not None
        np.testing.assert_allclose(comp.f_ev, comp.f / RY_TO_EV)

    def test_to_dataframe_energy_ev_column(self) -> None:
        """to_dataframe() energy_eV column equals energy_Ry * RY_TO_EV."""
        comp = _make_dos_component()
        df = comp.to_dataframe()
        np.testing.assert_allclose(df["energy_eV"].to_numpy(), df["energy_Ry"].to_numpy() * RY_TO_EV)


class TestGOIterationEvProperties:
    """Tests for GOIteration eV-unit properties."""

    def test_total_energy_ev(self) -> None:
        """total_energy_ev returns total_energy scaled by RY_TO_EV."""
        it = GOIteration(iteration=1, neu=0.0, moment=2.2, total_energy=-2520.6, rms_error=-4.5)
        assert it.total_energy_ev == pytest.approx(it.total_energy * RY_TO_EV)


class TestDOSCurveEvProperties:
    """Tests for DOSCurve eV-unit properties."""

    def _make_curve(self) -> DOSCurve:
        return DOSCurve(
            spin="up",
            energy=np.linspace(-0.5, 0.5, 5),
            values=np.ones(5) * 2.0,
        )

    def test_energy_ev(self) -> None:
        """energy_ev returns energy array scaled by RY_TO_EV."""
        curve = self._make_curve()
        np.testing.assert_allclose(curve.energy_ev, curve.energy * RY_TO_EV)

    def test_values_ev(self) -> None:
        """values_ev returns DOS values divided by RY_TO_EV."""
        curve = self._make_curve()
        np.testing.assert_allclose(curve.values_ev, curve.values / RY_TO_EV)


def _make_base_kwargs() -> dict:
    return {
        "date": "2025-01-01",
        "time": "00:00:00",
        "meshr": 400,
        "mse": 5,
        "ng": 21,
        "mxl": 3,
        "input_params": InputParams(
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
        "energy_mesh": [],
        "lattice": LatticeInfo(
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
        "atom_types": [AtomType(name="Fe", rmt=0.4, field=0.0, lmxtyp=2, components=[AtomicComponent(anclr=26.0, conc=1.0)])],
        "positions": [],
        "core_configs": [],
        "atomic_properties": [],
        "system_info": SystemInfo(os="Linux", host="host", machine="x86_64", num_cores=4, elapsed_time=1.0, num_threads=4),
    }


def _make_go_result() -> GOResult:
    iterations = [
        GOIteration(iteration=1, neu=0.01, moment=2.1, total_energy=-2520.5, rms_error=-3.0),
        GOIteration(iteration=2, neu=0.00, moment=2.2, total_energy=-2520.6, rms_error=-4.5),
    ]
    return GOResult(**_make_base_kwargs(), iterations=iterations, converged=True)


class TestGOResultToDataframe:
    """Tests for GOResult.to_dataframe()."""

    def test_columns(self) -> None:
        """to_dataframe() returns exactly the expected column names in order."""
        df = _make_go_result().to_dataframe()
        assert list(df.columns) == ["neu", "moment", "total_energy_Ry", "total_energy_eV", "rms_error"]

    def test_row_count(self) -> None:
        """to_dataframe() produces one row per SCF iteration."""
        r = _make_go_result()
        assert len(r.to_dataframe()) == len(r.iterations)

    def test_empty_iterations(self) -> None:
        """to_dataframe() on an empty iteration list returns empty DataFrame with correct columns."""
        r = dataclasses.replace(_make_go_result(), iterations=[])
        df = r.to_dataframe()
        assert len(df) == 0
        assert "total_energy_Ry" in df.columns

    def test_energy_ev_column(self) -> None:
        """total_energy_eV equals total_energy_Ry * RY_TO_EV."""
        df = _make_go_result().to_dataframe()
        np.testing.assert_allclose(df["total_energy_eV"].to_numpy(), df["total_energy_Ry"].to_numpy() * RY_TO_EV)

    def test_values(self) -> None:
        """Moments are stored correctly."""
        r = _make_go_result()
        df = r.to_dataframe()
        assert df["moment"].tolist() == pytest.approx([it.moment for it in r.iterations])


class TestCalculationResultToDictToJson:
    """Tests for CalculationResult.to_dict() / to_json()."""

    def test_go_to_dict_json_roundtrip(self, fe_go: Path) -> None:
        """GOResult.to_json() round-trips through json.loads()."""
        r = parse_go(fe_go)
        text = r.to_json()
        assert isinstance(text, str)
        parsed = json.loads(text)
        assert parsed["converged"] == r.converged

    def test_go_to_dict_iterations(self, fe_go: Path) -> None:
        """GOResult.to_dict() preserves the SCF iteration history."""
        r = parse_go(fe_go)
        d = r.to_dict()
        assert len(d["iterations"]) == len(r.iterations)
        assert d["iterations"][0]["moment"] == pytest.approx(r.iterations[0].moment)

    def test_dos_to_dict_json_roundtrip(self, fe_dos: Path) -> None:
        """DOSResult.to_json() round-trips through json.loads()."""
        r = parse_dos(fe_dos)
        text = r.to_json()
        assert isinstance(text, str)
        parsed = json.loads(text)
        assert len(parsed["dos_components"]) == len(r.dos_components)

    def test_dos_component_energy_becomes_plain_list(self, fe_dos: Path) -> None:
        """DOSComponent.energy (a numpy array) is serialized as a plain list."""
        r = parse_dos(fe_dos)
        d = r.to_dict()
        energy = d["dos_components"][0]["energy"]
        assert isinstance(energy, list)
        assert energy == pytest.approx(r.dos_components[0].energy.tolist())

    def test_dos_to_json_indent_kwarg(self, fe_dos: Path) -> None:
        """to_json() forwards keyword arguments to json.dumps()."""
        r = parse_dos(fe_dos)
        text = r.to_json(indent=2)
        assert isinstance(text, str)
        assert "\n" in text

    def test_to_json_no_path_returns_string(self, fe_dos: Path) -> None:
        """to_json() without a path returns the JSON string."""
        r = parse_dos(fe_dos)
        assert isinstance(r.to_json(), str)

    def test_to_json_with_path_writes_file_and_returns_none(self, fe_dos: Path, tmp_path: Path) -> None:
        """to_json(path) writes the JSON to disk and returns None."""
        r = parse_dos(fe_dos)
        out = tmp_path / "dos.json"
        result = r.to_json(out, indent=2)
        assert result is None
        assert json.loads(out.read_text()) == r.to_dict()

    def test_spc_to_dict_json_roundtrip(self, fe_spc: Path) -> None:
        """SPCResult.to_json() round-trips through json.loads()."""
        r = parse_spc(fe_spc)
        text = r.to_json()
        assert isinstance(text, str)
        parsed = json.loads(text)
        assert parsed["spc_params"]["nk"] == r.spc_params.nk

    def test_spc_spectral_function_data_becomes_plain_list(self, fe_spc: Path) -> None:
        """SpectralFunction.data (a numpy array) is serialized as a plain nested list."""
        r = parse_spc(fe_spc)
        d = r.to_dict()
        if r.spectral_up is not None and r.spectral_up.data is not None:
            data = d["spectral_up"]["data"]
            assert isinstance(data, list)
            assert isinstance(data[0], list)
