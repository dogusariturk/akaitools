"""Tests for InputFile construction and rendering."""

from __future__ import annotations

from pathlib import Path

import pytest

from akaitools import InputFile, KPath, KPoint, parse_go, parse_spc
from akaitools.errors import InputValidationError
from akaitools.models import AtomicComponent, AtomPosition, AtomType


def _fe_atom_types() -> list[AtomType]:
    return [AtomType(name="Fe", rmt=0.0, field=0.0, lmxtyp=2, components=[AtomicComponent(anclr=26.0, conc=1.0)])]


def _fe_positions() -> list[AtomPosition]:
    return [AtomPosition(x=0.0, y=0.0, z=0.0, atom_type="Fe")]


def _minimal_fe(**kwargs) -> InputFile:
    defaults: dict = {
        "mode": "go",
        "data_file": "data/fe",
        "bravais": "bcc",
        "a": 5.27,
        "atom_types": _fe_atom_types(),
        "positions": _fe_positions(),
    }
    defaults.update(kwargs)
    return InputFile(**defaults)


def _nife_atom_types() -> list[AtomType]:
    return [
        AtomType(
            name="NiFe",
            rmt=0.0,
            field=0.0,
            lmxtyp=2,
            components=[
                AtomicComponent(anclr=28.0, conc=0.5),
                AtomicComponent(anclr=26.0, conc=0.5),
            ],
        )
    ]


def _spc_fe_with_kpath(kpath: KPath) -> InputFile:
    return InputFile(
        mode="spc",
        data_file="data/fe",
        bravais="bcc",
        a=5.27,
        atom_types=_fe_atom_types(),
        positions=_fe_positions(),
        kpath=kpath,
    )


def test_input_file_importable_from_package() -> None:
    """InputFile is accessible via the top-level package namespace."""
    assert InputFile is not None


def test_kpoint_importable_from_package() -> None:
    """KPoint is accessible via the top-level package namespace."""
    assert KPoint is not None


def test_kpath_importable_from_package() -> None:
    """KPath is accessible via the top-level package namespace."""
    assert KPath is not None


def test_scratch_to_string_contains_mode() -> None:
    """Rendered text includes the calculation mode keyword."""
    assert "go" in _minimal_fe().to_string()


def test_scratch_to_string_contains_bravais() -> None:
    """Rendered text includes the Bravais lattice type."""
    assert "bcc" in _minimal_fe().to_string()


def test_scratch_to_string_contains_lattice_constant() -> None:
    """Rendered text includes the lattice constant value."""
    assert "5.27" in _minimal_fe().to_string()


def test_scratch_to_string_contains_atom_type_name() -> None:
    """Rendered text includes the atom-type name."""
    assert "Fe" in _minimal_fe().to_string()


def test_scratch_to_string_ends_with_newline() -> None:
    """Rendered text is terminated by a newline character."""
    assert _minimal_fe().to_string().endswith("\n")


def test_scratch_default_lattice_params_render_as_commas() -> None:
    """Optional lattice parameters at their defaults render as commas."""
    text = _minimal_fe().to_string()
    lattice_line = next(ln for ln in text.splitlines() if "bcc" in ln)
    assert "," in lattice_line


def test_scratch_nontrivial_c_over_a_renders_as_number() -> None:
    """A non-default c/a ratio is rendered as a numeric value, not a comma."""
    assert "1.63" in _minimal_fe(bravais="hexagonal", c_over_a=1.63).to_string()


def test_scratch_title_appears_on_first_line() -> None:
    """An explicit title is placed on the first comment line."""
    assert _minimal_fe(title="My custom title").to_string().startswith("c--- My custom title ---")


def test_scratch_auto_title_uses_bravais_and_type() -> None:
    """When title is empty the first line is auto-derived from bravais and atom type."""
    first_line = _minimal_fe(title="").to_string().splitlines()[0]
    assert "BCC" in first_line and "Fe" in first_line


def test_go_mode_has_end_marker() -> None:
    """GO-mode input ends with the required 'end' marker."""
    assert " end" in _minimal_fe(mode="go").to_string()


def test_dos_mode_has_end_marker() -> None:
    """DOS-mode input ends with the required 'end' marker."""
    assert " end" in _minimal_fe(mode="dos").to_string()


def test_scratch_end_marker_present() -> None:
    """The 'end' keyword appears in a default GO input."""
    assert " end" in _minimal_fe().to_string()


def test_scratch_ntyp_block_correct() -> None:
    """The ntyp block contains the correct number of site types."""
    assert "\n     1\n" in _minimal_fe().to_string()


def test_scratch_natm_block_correct() -> None:
    """The natm block contains the correct number of atoms."""
    assert "\n     1\n" in _minimal_fe().to_string()


def test_invalid_mode_raises() -> None:
    """An unrecognised mode raises InputValidationError with field='mode'."""
    with pytest.raises(InputValidationError) as exc_info:
        _minimal_fe(mode="xyz")
    assert exc_info.value.field == "mode"


def test_empty_atom_types_raises() -> None:
    """An empty atom_types list raises InputValidationError."""
    with pytest.raises(InputValidationError) as exc_info:
        _minimal_fe(atom_types=[])
    assert exc_info.value.field == "atom_types"


def test_empty_positions_raises() -> None:
    """An empty positions list raises InputValidationError."""
    with pytest.raises(InputValidationError) as exc_info:
        _minimal_fe(positions=[])
    assert exc_info.value.field == "positions"


def test_atom_type_with_no_components_raises() -> None:
    """An AtomType with no components raises InputValidationError naming the type."""
    bad_types = [AtomType(name="Fe", rmt=0.0, field=0.0, lmxtyp=2, components=[])]
    with pytest.raises(InputValidationError) as exc_info:
        _minimal_fe(atom_types=bad_types)
    assert "atom_types[Fe].components" in exc_info.value.field


def test_concentration_not_summing_to_one_raises() -> None:
    """Component concentrations that don't sum to 1.0 raise InputValidationError."""
    bad_types = [
        AtomType(
            name="NiFe",
            rmt=0.0,
            field=0.0,
            lmxtyp=2,
            components=[
                AtomicComponent(anclr=28.0, conc=0.3),
                AtomicComponent(anclr=26.0, conc=0.3),
            ],
        )
    ]
    with pytest.raises(InputValidationError) as exc_info:
        _minimal_fe(atom_types=bad_types, positions=[AtomPosition(0, 0, 0, "NiFe")])
    assert "atom_types[NiFe].components" in exc_info.value.field


def test_position_references_undefined_type_raises() -> None:
    """A position that names an undefined atom type raises InputValidationError."""
    with pytest.raises(InputValidationError) as exc_info:
        _minimal_fe(positions=[AtomPosition(x=0.0, y=0.0, z=0.0, atom_type="Xx")])
    assert "positions[0].atom_type" in exc_info.value.field


def test_kpath_with_non_spc_mode_raises() -> None:
    """Supplying a kpath for a non-SPC mode raises InputValidationError with field='kpath'."""
    kp = KPath(nkpts=100, points=[KPoint("0", "0", "0")])
    with pytest.raises(InputValidationError) as exc_info:
        _minimal_fe(kpath=kp)
    assert exc_info.value.field == "kpath"


def test_single_component_inline_format() -> None:
    """Single-component site renders anclr and conc on the same line as the type."""
    text = _minimal_fe().to_string()
    fe_line = next(ln for ln in text.splitlines() if ln.strip().startswith("Fe"))
    assert "26" in fe_line
    assert "100" in fe_line


def test_cpa_type_uses_continuation_lines() -> None:
    """CPA site with multiple components renders components on continuation lines."""
    inp = InputFile(
        mode="go",
        data_file="data/nife",
        bravais="fcc",
        a=6.55,
        atom_types=_nife_atom_types(),
        positions=[AtomPosition(0, 0, 0, "NiFe")],
    )
    text = inp.to_string()
    nife_line = next(ln for ln in text.splitlines() if ln.strip().startswith("NiFe"))
    assert "28" not in nife_line
    assert "26" not in nife_line
    assert "28" in text
    assert "26" in text


def test_cpa_concentration_percent_conversion() -> None:
    """CPA component concentrations are converted from fractions to integer percent."""
    inp = InputFile(
        mode="go",
        data_file="data/nife",
        bravais="fcc",
        a=6.55,
        atom_types=_nife_atom_types(),
        positions=[AtomPosition(0, 0, 0, "NiFe")],
    )
    assert "50" in inp.to_string()


def test_single_component_concentration_percent_conversion() -> None:
    """Single-component concentration 1.0 renders as 100."""
    assert "100" in _minimal_fe().to_string()


def test_spc_kpath_block_present() -> None:
    """K-path nkpts and point coordinates appear in the rendered SPC input."""
    kp = KPath(nkpts=300, points=[KPoint("0", "0", "0"), KPoint("0", "1", "0")])
    text = _spc_fe_with_kpath(kp).to_string()
    assert "300" in text
    assert "0 1 0" in text


def test_spc_mode_has_no_end_marker() -> None:
    """SPC mode does not emit the 'end' keyword."""
    kp = KPath(nkpts=300, points=[KPoint("0", "0", "0")])
    assert " end" not in _spc_fe_with_kpath(kp).to_string()


def test_spc_nkpts_after_positions_block() -> None:
    """The nkpts value appears as the first line after the positions block."""
    kp = KPath(nkpts=300, points=[KPoint("0", "0", "0")])
    text = _spc_fe_with_kpath(kp).to_string()
    last_lines = text.strip().splitlines()
    nkpts_line = next(ln for ln in reversed(last_lines) if ln.strip() == "300")
    assert nkpts_line.strip() == "300"


def test_spc_fractional_coordinates_preserved() -> None:
    """Fractional coordinate strings are written verbatim to the k-path block."""
    kp = KPath(nkpts=100, points=[KPoint("1/2", "1/2", "0")])
    assert "1/2 1/2 0" in _spc_fe_with_kpath(kp).to_string()


def test_spc_no_kpath_no_kpath_block() -> None:
    """SPC mode with kpath=None emits neither 'end' nor a k-path block."""
    inp = InputFile(
        mode="spc",
        data_file="data/fe",
        bravais="bcc",
        a=5.27,
        atom_types=_fe_atom_types(),
        positions=_fe_positions(),
        kpath=None,
    )
    text = inp.to_string()
    assert " end" not in text
    assert "300" not in text


def test_spc_all_kpoints_rendered() -> None:
    """All k-points in the path are written to the file, one per line."""
    n_points = 6
    points = [
        KPoint("0", "0", "0", label="Γ"),
        KPoint("0", "1", "0", label="H"),
        KPoint("1/2", "1/2", "0", label="N"),
        KPoint("1/2", "1/2", "1/2", label="P"),
        KPoint("0", "0", "0", label="Γ"),
        KPoint("1/2", "1/2", "0", label="N"),
    ]
    kp = KPath(nkpts=300, points=points)
    text = _spc_fe_with_kpath(kp).to_string()
    assert " end" not in text
    sep = "c" + "-" * 60
    after_last_sep = text.split(sep)[-1].strip().splitlines()
    assert len(after_last_sep) == 1 + n_points


def test_from_result_fe_go_mode(fe_go: Path) -> None:
    """Mode is correctly reconstructed from a GO result."""
    assert InputFile.from_result(parse_go(fe_go)).mode == "go"


def test_from_result_fe_go_bravais(fe_go: Path) -> None:
    """Bravais lattice type is correctly reconstructed from a GO result."""
    assert InputFile.from_result(parse_go(fe_go)).bravais == "bcc"


def test_from_result_fe_go_lattice_constant(fe_go: Path) -> None:
    """Lattice constant is correctly reconstructed from a GO result."""
    assert InputFile.from_result(parse_go(fe_go)).a == pytest.approx(5.27, rel=1e-4)


def test_from_result_fe_go_single_atom_type(fe_go: Path) -> None:
    """Fe GO result produces exactly one atom type named 'Fe'."""
    inp = InputFile.from_result(parse_go(fe_go))
    assert len(inp.atom_types) == 1
    assert inp.atom_types[0].name == "Fe"


def test_from_result_reset_rmt_default(fe_go: Path) -> None:
    """By default from_result preserves the computed muffin-tin radii."""
    result = parse_go(fe_go)
    original_rmt = result.atom_types[0].rmt
    assert InputFile.from_result(result).atom_types[0].rmt == pytest.approx(original_rmt)


def test_from_result_reset_rmt_true(fe_go: Path) -> None:
    """Explicit reset_rmt=True zeroes all muffin-tin radii."""
    for at in InputFile.from_result(parse_go(fe_go), reset_rmt=True).atom_types:
        assert at.rmt == 0.0


def test_from_result_reset_rmt_false_preserves_value(fe_go: Path) -> None:
    """reset_rmt=False preserves the computed muffin-tin radii from the result."""
    result = parse_go(fe_go)
    original_rmt = result.atom_types[0].rmt
    assert InputFile.from_result(result, reset_rmt=False).atom_types[0].rmt == pytest.approx(original_rmt)


def test_from_result_nife_cpa_two_components(nife_go: Path) -> None:
    """CPA site in NiFe result reconstructs with two components."""
    assert len(InputFile.from_result(parse_go(nife_go)).atom_types[0].components) == 2


def test_from_result_gaas_four_types(gaas_go: Path) -> None:
    """GaAs result reconstructs with four atom types."""
    assert len(InputFile.from_result(parse_go(gaas_go)).atom_types) == 4


def test_from_result_gaas_four_positions(gaas_go: Path) -> None:
    """GaAs result reconstructs with four atom positions."""
    assert len(InputFile.from_result(parse_go(gaas_go)).positions) == 4


def test_from_result_gaas_ntyp_in_output(gaas_go: Path) -> None:
    """GaAs ntyp block in rendered output contains 4."""
    assert "\n     4\n" in InputFile.from_result(parse_go(gaas_go)).to_string()


def test_from_result_mode_override(fe_go: Path) -> None:
    """Mode can be overridden to 'spc' when reconstructing from a GO result."""
    assert InputFile.from_result(parse_go(fe_go), mode="spc").mode == "spc"


def test_from_result_mode_override_dos(fe_go: Path) -> None:
    """Mode can be overridden to 'dos' when reconstructing from a GO result."""
    assert InputFile.from_result(parse_go(fe_go), mode="dos").mode == "dos"


def test_from_result_invalid_mode_raises(fe_go: Path) -> None:
    """An invalid mode override raises InputValidationError with field='mode'."""
    with pytest.raises(InputValidationError) as exc_info:
        InputFile.from_result(parse_go(fe_go), mode="bad")
    assert exc_info.value.field == "mode"


def test_from_result_with_kpath(fe_go: Path) -> None:
    """A kpath supplied to from_result renders correctly in SPC mode."""
    kp = KPath(
        nkpts=300,
        points=[KPoint("0", "0", "0"), KPoint("0", "1", "0"), KPoint("1/2", "1/2", "0")],
    )
    text = InputFile.from_result(parse_go(fe_go), mode="spc", kpath=kp).to_string()
    assert "300" in text
    assert "0 1 0" in text
    assert "1/2 1/2 0" in text


def test_from_result_spc_roundtrip_mode(fe_spc: Path) -> None:
    """Reconstructing from an SPC result preserves the 'spc' mode."""
    assert InputFile.from_result(parse_spc(fe_spc)).mode == "spc"


def test_write_creates_file(tmp_path: Path, fe_go: Path) -> None:
    """write() creates the file at the specified path."""
    out = tmp_path / "fe_input"
    InputFile.from_result(parse_go(fe_go)).write(out)
    assert out.exists()


def test_write_file_starts_with_comment(tmp_path: Path, fe_go: Path) -> None:
    """The written file starts with the title comment line."""
    out = tmp_path / "fe_input"
    InputFile.from_result(parse_go(fe_go)).write(out)
    assert out.read_text().startswith("c---")


def test_write_content_matches_to_string(tmp_path: Path, fe_go: Path) -> None:
    """File content written by write() is identical to to_string()."""
    inp = InputFile.from_result(parse_go(fe_go))
    out = tmp_path / "fe_input"
    inp.write(out)
    assert out.read_text() == inp.to_string()


def test_roundtrip_single_component_go() -> None:
    """A single-component GO input round-trips through to_string()/from_string()."""
    original = _minimal_fe()
    parsed = InputFile.from_string(original.to_string())
    assert parsed.to_string() == original.to_string()


def test_roundtrip_cpa_multi_component() -> None:
    """A multi-component CPA site round-trips through to_string()/from_string()."""
    original = InputFile(
        mode="go",
        data_file="data/nife",
        bravais="fcc",
        a=6.55,
        atom_types=_nife_atom_types(),
        positions=[AtomPosition(0, 0, 0, "NiFe")],
    )
    parsed = InputFile.from_string(original.to_string())
    assert parsed.to_string() == original.to_string()
    assert [c.anclr for c in parsed.atom_types[0].components] == [28.0, 26.0]
    assert [c.conc for c in parsed.atom_types[0].components] == [0.5, 0.5]


def test_roundtrip_dos_mode() -> None:
    """A DOS-mode input round-trips through to_string()/from_string()."""
    original = _minimal_fe(mode="dos")
    parsed = InputFile.from_string(original.to_string())
    assert parsed.to_string() == original.to_string()
    assert parsed.mode == "dos"


def test_roundtrip_multi_site_structure() -> None:
    """A multi-site structure with vacancies round-trips through to_string()/from_string()."""
    original = InputFile(
        mode="go",
        data_file="data/gaas",
        bravais="fcc",
        a=10.684,
        reltyp="sra",
        sdftyp="mjw",
        bzqlty=4,
        atom_types=[
            AtomType("Ga", rmt=0.0, field=0.0, lmxtyp=2, components=[AtomicComponent(31.0, 1.0)]),
            AtomType("As", rmt=0.0, field=0.0, lmxtyp=2, components=[AtomicComponent(33.0, 1.0)]),
            AtomType("Vc1", rmt=0.0, field=0.0, lmxtyp=0, components=[AtomicComponent(0.0, 1.0)]),
            AtomType("Vc2", rmt=0.0, field=0.0, lmxtyp=0, components=[AtomicComponent(0.0, 1.0)]),
        ],
        positions=[
            AtomPosition(0.00, 0.00, 0.00, "Ga"),
            AtomPosition(0.25, 0.25, 0.25, "As"),
            AtomPosition(0.50, 0.50, 0.50, "Vc1"),
            AtomPosition(0.75, 0.75, 0.75, "Vc2"),
        ],
    )
    parsed = InputFile.from_string(original.to_string())
    assert parsed.to_string() == original.to_string()
    assert [at.name for at in parsed.atom_types] == ["Ga", "As", "Vc1", "Vc2"]
    assert len(parsed.positions) == 4


def test_roundtrip_spc_mode_with_kpath() -> None:
    """An SPC input with a k-path round-trips; coordinates survive, labels become None."""
    points = [
        KPoint("0", "0", "0", label="Γ"),
        KPoint("0", "1", "0", label="H"),
        KPoint("1/2", "1/2", "0", label="N"),
        KPoint("1/2", "1/2", "1/2", label="P"),
    ]
    kp = KPath(nkpts=300, points=points)
    original = _spc_fe_with_kpath(kp)
    parsed = InputFile.from_string(original.to_string())
    assert parsed.to_string() == original.to_string()
    assert parsed.kpath is not None
    assert parsed.kpath.nkpts == 300
    assert [(pt.x, pt.y, pt.z) for pt in parsed.kpath.points] == [(pt.x, pt.y, pt.z) for pt in points]
    assert all(pt.label is None for pt in parsed.kpath.points)


def test_roundtrip_spc_mode_without_kpath() -> None:
    """An SPC input with kpath=None round-trips with kpath staying None."""
    original = InputFile(
        mode="spc",
        data_file="data/fe",
        bravais="bcc",
        a=5.27,
        atom_types=_fe_atom_types(),
        positions=_fe_positions(),
        kpath=None,
    )
    parsed = InputFile.from_string(original.to_string())
    assert parsed.to_string() == original.to_string()
    assert parsed.kpath is None


def test_roundtrip_via_from_file(tmp_path: Path) -> None:
    """from_file() reads a written file and reproduces the same rendered text."""
    original = _minimal_fe()
    out = tmp_path / "fe.in"
    original.write(out)
    parsed = InputFile.from_file(out)
    assert parsed.to_string() == original.to_string()


def test_from_string_malformed_mode_line_raises() -> None:
    """A mode line missing the data_file token raises InputValidationError."""
    text = _minimal_fe().to_string().replace("    go   data/fe", "    go")
    with pytest.raises(InputValidationError) as exc_info:
        InputFile.from_string(text)
    assert exc_info.value.field == "mode"


def test_from_string_non_numeric_lattice_constant_raises() -> None:
    """A non-numeric lattice constant raises InputValidationError naming 'a'."""
    text = _minimal_fe().to_string().replace("5.27", "notanumber")
    with pytest.raises(InputValidationError) as exc_info:
        InputFile.from_string(text)
    assert exc_info.value.field == "a"


def test_from_string_missing_component_line_raises() -> None:
    """Truncated CPA component data raises InputValidationError."""
    original = InputFile(
        mode="go",
        data_file="data/nife",
        bravais="fcc",
        a=6.55,
        atom_types=_nife_atom_types(),
        positions=[AtomPosition(0, 0, 0, "NiFe")],
    )
    lines = original.to_string().splitlines()
    truncated = "\n".join(line for line in lines if "26" not in line) + "\n"
    with pytest.raises(InputValidationError) as exc_info:
        InputFile.from_string(truncated)
    assert "components" in exc_info.value.field


def test_parse_real_gaas_input_file() -> None:
    """A hand-written AkaiKKR input fixture file parses successfully."""
    path = Path(__file__).parent / "data" / "in" / "gaas"
    inp = InputFile.from_file(path)
    assert inp.mode == "go"
    assert inp.bravais == "fcc"
    assert inp.a == pytest.approx(10.684)
    assert inp.reltyp == "sra"
    assert inp.sdftyp == "mjw"
    assert inp.bzqlty == 4
    assert inp.pmix == pytest.approx(0.035)
    assert [at.name for at in inp.atom_types] == ["Ga", "As", "Vc1", "Vc2"]
    assert len(inp.positions) == 4
    assert inp.positions[1].atom_type == "As"
    assert inp.positions[1].x == pytest.approx(0.25)


def test_parse_aux_lattice_input_file() -> None:
    """An 'aux' lattice input (no title, primitive vectors, merged mixing token, direction-suffixed coordinates) parses successfully."""
    path = Path(__file__).parent / "data" / "in" / "aux_lattice"
    inp = InputFile.from_file(path)
    assert inp.mode == "go"
    assert inp.data_file == "data/synthetic"
    assert inp.bravais == "aux"
    assert inp.a == pytest.approx(1.0)
    assert inp.primitive_vectors is not None
    assert inp.primitive_vectors[0] == pytest.approx((3.0, 0.0, 0.0))
    assert inp.primitive_vectors[1] == pytest.approx((0.0, 3.0, 0.0))
    assert inp.primitive_vectors[2] == pytest.approx((0.0, 0.0, 4.0))
    assert inp.edelt == pytest.approx(0.001)
    assert inp.ewidth == pytest.approx(1.0)
    assert inp.reltyp == "nrl"
    assert inp.sdftyp == "vwn"
    assert inp.magtyp == "kick"
    assert inp.record == "2nd"
    assert inp.bzqlty == 6
    assert inp.maxitr == 50
    assert inp.pmix == pytest.approx(0.03)
    assert inp.mixtyp == "br"
    assert [at.name for at in inp.atom_types] == ["A", "B"]
    assert inp.atom_types[1].components[0].anclr == pytest.approx(14.0)
    assert len(inp.positions) == 2
    assert inp.positions[0].x == pytest.approx(0.0)
    assert inp.positions[1].y == pytest.approx(0.5)
    assert inp.positions[1].atom_type == "B"


def test_roundtrip_aux_lattice_input_file() -> None:
    """A parsed 'aux' lattice input re-parses identically after to_string()."""
    path = Path(__file__).parent / "data" / "in" / "aux_lattice"
    inp = InputFile.from_file(path)
    reparsed = InputFile.from_string(inp.to_string())
    assert reparsed.to_string() == inp.to_string()
    assert reparsed.bravais == inp.bravais
    assert reparsed.primitive_vectors == inp.primitive_vectors


def test_from_string_no_title_line() -> None:
    """A file with no leading title comment parses with an empty title."""
    text = _minimal_fe().to_string()
    text_without_title = "\n".join(ln for ln in text.splitlines() if not ln.startswith("c---")) + "\n"
    inp = InputFile.from_string(text_without_title)
    assert inp.title == ""
    assert inp.mode == "go"
    assert inp.bravais == "bcc"


def test_aux_bravais_without_primitive_vectors_raises() -> None:
    """Constructing an 'aux' InputFile without primitive_vectors raises InputValidationError."""
    with pytest.raises(InputValidationError) as exc_info:
        _minimal_fe(bravais="aux")
    assert exc_info.value.field == "primitive_vectors"


def test_non_aux_bravais_with_primitive_vectors_raises() -> None:
    """Supplying primitive_vectors for a non-aux/prv bravais raises InputValidationError."""
    with pytest.raises(InputValidationError) as exc_info:
        _minimal_fe(primitive_vectors=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
    assert exc_info.value.field == "primitive_vectors"


def test_from_string_pmix_with_mixtype_suffix() -> None:
    """A pmix token with a mixing-type suffix (e.g. '0.02br') splits into pmix and mixtyp."""
    text = _minimal_fe().to_string().replace("0.035", "0.02br")
    inp = InputFile.from_string(text)
    assert inp.pmix == pytest.approx(0.02)
    assert inp.mixtyp == "br"


def test_from_string_bzqlty_letter_code() -> None:
    """A letter-code bzqlty token (e.g. 't') parses without error."""
    text = _minimal_fe().to_string().replace("    update     8", "    update     t")
    inp = InputFile.from_string(text)
    assert inp.bzqlty == "t"


def test_from_string_position_with_direction_suffix() -> None:
    """Atomic-position coordinates carrying a redundant direction suffix (e.g. '0.5a') parse to plain floats."""
    text = _minimal_fe().to_string().replace("0        0          0", "0a       0b         0c")
    inp = InputFile.from_string(text)
    assert inp.positions[0].x == pytest.approx(0.0)
    assert inp.positions[0].y == pytest.approx(0.0)
    assert inp.positions[0].z == pytest.approx(0.0)
