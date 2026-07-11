"""Formatting of InputFile instances into AkaiKKR free-column input text."""

from __future__ import annotations

from typing import TYPE_CHECKING

from akaitools.input.lattice import is_aux_or_prv

if TYPE_CHECKING:
    from akaitools.input.model import InputFile


def _flt(value: float) -> str:
    """Format a float, preserving at least one decimal place."""
    s = f"{value:g}"
    return s if ("." in s or "e" in s) else s + ".0"


def _opt(value: float, default: float) -> str:
    """Return the value as a string or ``","`` when it equals the default."""
    return _flt(value) if value != default else ","


def format_input_file(inp: InputFile) -> str:
    """Format an ``InputFile`` as a string in AkaiKKR free-column format.

    Args:
        inp: The input file to format.

    Returns:
        The complete input file text, terminated by a newline.
    """
    title = inp.title or f"{inp.bravais.upper()} {inp.atom_types[0].name}"
    sep = "c" + "-" * 60

    if is_aux_or_prv(inp.bravais):
        assert inp.primitive_vectors is not None
        v1, v2, v3 = inp.primitive_vectors
        lattice_block = [
            "c   brvtyp     primitive vectors (v1/v2/v3, one per line)",
            f"    {inp.bravais:<10s} {v1[0]:<10g} {v1[1]:<10g} {v1[2]:<10g}",
            f"               {v2[0]:<10g} {v2[1]:<10g} {v2[2]:<10g}",
            f"               {v3[0]:<10g} {v3[1]:<10g} {v3[2]:<10g}",
            "c   a",
            f"    {inp.a:<8g}",
        ]
    else:
        lat_line = (
            f"    {inp.bravais:<10s} {inp.a:<8g}"
            f" {_opt(inp.c_over_a, 1.0):<6s}"
            f" {_opt(inp.b_over_a, 1.0):<6s}"
            f" {_opt(inp.alpha, 90.0):<7s}"
            f" {_opt(inp.beta, 90.0):<5s}"
            f" {_opt(inp.gamma, 90.0):<7s}"
            f" ,"
        )
        lattice_block = [
            "c   brvtyp     a        c/a   b/a   alpha   beta   gamma",
            lat_line,
        ]

    lines = [
        f"c--- {title} ---",
        f"    {inp.mode}   {inp.data_file}",
        sep,
        *lattice_block,
        sep,
        "c   edelt    ewidth    reltyp   sdftyp   magtyp   record",
        f"    {_flt(inp.edelt):<9s} {_flt(inp.ewidth):<9s} {inp.reltyp:<9s} {inp.sdftyp:<9s} {inp.magtyp:<9s} {inp.record}",
        sep,
        "c   outtyp    bzqlty   maxitr   pmix",
        f"    {inp.outtyp:<10s} {str(inp.bzqlty):<8s} {inp.maxitr:<8d} {inp.pmix:g}{inp.mixtyp}",
        sep,
        "c    ntyp",
        f"     {len(inp.atom_types)}",
        sep,
        "c   type    ncmp    rmt    field   mxl  anclr   conc",
    ]

    for at in inp.atom_types:
        ncmp = len(at.components)
        first = f"    {at.name:<8s} {ncmp:<7d} {at.rmt:<7g} {at.field:<7.1f} {at.lmxtyp}"
        if ncmp == 1:
            comp = at.components[0]
            lines.append(f"{first}  {int(comp.anclr):>5d}  {round(comp.conc * 100):>5d}")
        else:
            lines.append(first)
            for comp in at.components:
                lines.append(f"{'':>42s}{int(comp.anclr):>5d}  {round(comp.conc * 100):>5d}")

    lines += [
        sep,
        "c   natm",
        f"     {len(inp.positions)}",
        sep,
        "c   atmicx(in the unit of a)     atmtyp",
    ]

    for pos in inp.positions:
        lines.append(f"     {pos.x:<10g} {pos.y:<10g} {pos.z:<10g} {pos.atom_type}")

    lines.append(sep)

    if inp.mode != "spc":
        lines.append(" end")
    elif inp.kpath is not None:
        lines.append(f" {inp.kpath.nkpts}")
        for pt in inp.kpath.points:
            lines.append(f" {pt.x} {pt.y} {pt.z}")

    return "\n".join(lines) + "\n"
