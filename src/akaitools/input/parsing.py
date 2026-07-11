"""Parsing of AkaiKKR free-column input files into InputFile instances."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from akaitools.errors import InputValidationError
from akaitools.input.lattice import is_aux_or_prv
from akaitools.models import AtomicComponent, AtomPosition, AtomType, KPath, KPoint

if TYPE_CHECKING:
    from akaitools.input.model import InputFile


def _parse_float(token: str, field: str) -> float:
    """Parse a token as a float, raising ``InputValidationError`` on failure."""
    try:
        return float(token)
    except ValueError as exc:
        raise InputValidationError(field, f"expected a number, got {token!r}") from exc


def _parse_int(token: str, field: str) -> int:
    """Parse a token as an int, raising ``InputValidationError`` on failure."""
    try:
        return int(token)
    except ValueError as exc:
        raise InputValidationError(field, f"expected an integer, got {token!r}") from exc


def _parse_opt(token: str, default: float, field: str) -> float:
    """Parse a lattice-parameter token, mapping ``","`` back to ``default``."""
    if token == ",":
        return default
    return _parse_float(token, field)


def _parse_coord(token: str, field: str) -> float:
    """Parse an atomic-position coordinate, tolerating a trailing direction letter.

    AkaiKKR allows coordinates like ``"0.5a"`` (meaning ``0.5`` times primitive
    vector ``a``) alongside plain numbers. The direction is redundant when it
    matches the coordinate's own axis (the common case), so it is stripped and
    discarded; only the numeric value is kept.

    Args:
        token: The raw coordinate token.
        field: Field name to attach to the error if the token isn't numeric.

    Returns:
        The parsed coordinate value.
    """
    match = re.match(r"^(.+?)([abcxyzABCXYZ])$", token)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return _parse_float(token, field)


def _split_pmix(token: str, field: str) -> tuple[float, str]:
    """Split a combined mixing-parameter token into its value and mixing-type suffix.

    Args:
        token: The raw ``pmxtyp`` token, e.g. ``"0.035"`` or ``"0.02br"``.
        field: Field name to attach to the error if the token isn't numeric.

    Returns:
        A ``(pmix, mixtyp)`` tuple. ``mixtyp`` is ``""`` when no suffix is present.

    Raises:
        InputValidationError: If the token has no leading numeric value.
    """
    match = re.match(r"^([+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eEdD][+-]?\d+)?)(.*)$", token)
    if not match:
        raise InputValidationError(field, f"expected a mixing parameter, got {token!r}")
    value, mixtyp = match.groups()
    return _parse_float(value.replace("d", "e").replace("D", "e"), field), mixtyp


def _parse_bzqlty(token: str) -> int | str:
    """Parse a BZ-mesh-quality token, accepting either an integer or a quality letter code.

    AkaiKKR treats ``bzqlty`` as a free string that is either an integer mesh count
    or one of the quality codes ``t``/``l``/``m``/``h``/``u``.

    Args:
        token: The raw ``bzqlty`` token.

    Returns:
        The parsed integer, or the lowercased token if it isn't numeric.
    """
    try:
        return int(token)
    except ValueError:
        return token.lower()


class _Cursor:
    """A forward-only reader over input-file lines that skips comments and blanks.

    A line is a comment only when its very first character is ``c``, ``C``, or
    ``#`` (AkaiKKR's own rule) — leading whitespace before those characters does
    not count, so indented data is never mistaken for a comment.
    """

    def __init__(self, lines: list[str], start: int = 0) -> None:
        self._lines = lines
        self._idx = start

    def next(self, field: str) -> str:
        """Return the next non-comment, non-blank line.

        Args:
            field: Field name to attach to the error if no more data lines
                remain.

        Returns:
            The next data line.

        Raises:
            InputValidationError: If no data lines remain.
        """
        line = self.next_optional()
        if line is None:
            raise InputValidationError(field, "unexpected end of input; expected more data")
        return line

    def next_optional(self) -> str | None:
        """Return the next non-comment, non-blank line, or ``None`` if exhausted.

        Returns:
            The next data line, or ``None`` if no data lines remain.
        """
        while self._idx < len(self._lines):
            line = self._lines[self._idx]
            self._idx += 1
            if not line.strip() or line[:1] in ("c", "C", "#"):
                continue
            return line
        return None


def parse_input_file(cls: type[InputFile], text: str) -> InputFile:
    """Parse an AkaiKKR free-column input file into an ``InputFile``.

    This is the inverse of ``format_input_file()``: it reads an optional title
    comment, mode/data_file line, lattice line, energy/relativistic line,
    outtyp/bzqlty/maxitr/pmix line, atom-type block, and position block,
    following the same free-format conventions ``format_input_file()`` writes
    (whitespace-separated tokens, ``","`` meaning "use the default" for
    optional lattice parameters). Separator lines and comment
    lines — any line whose first character is ``"c"``, ``"C"``, or
    ``"#"`` — are skipped as structural landmarks only, matching
    AkaiKKR's own comment rule. A title comment is optional: AkaiKKR
    itself has no concept of one, so it is only captured when the very
    first line happens to be a comment.

    When ``bravais`` is ``"aux"`` or ``"prv"``, the three primitive
    vectors are read in place of ``c/a``, ``b/a``, and the lattice
    angles, matching AkaiKKR's own special-case handling of those
    lattice types.

    For ``mode == "spc"``, any content after the position block other than
    a bare ``"end"`` line is parsed as a ``KPath``: the first line is
    ``nkpts`` and the remaining lines are ``x y z`` k-point triples.
    ``format_input_file()`` never writes k-point labels, so parsed ``KPoint``
    instances always have ``label=None`` — this is an unrecoverable
    round-trip limitation.

    Args:
        cls: The ``InputFile`` class to construct (passed explicitly to
            avoid a circular import between this module and ``model``).
        text: The full input-file text.

    Returns:
        The parsed ``InputFile``.

    Raises:
        InputValidationError: If the text is malformed — wrong token
            counts, non-numeric values where numbers are expected, or a
            structural constraint from ``__post_init__`` is violated.
    """
    lines = text.splitlines()

    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    title = ""
    if idx < len(lines) and lines[idx][:1] in ("c", "C", "#"):
        title = lines[idx][1:].strip(" -")
        idx += 1

    cursor = _Cursor(lines, idx)

    mode_tokens = cursor.next("mode").split()
    if len(mode_tokens) < 2:
        raise InputValidationError("mode", f"expected 'mode data_file', got {mode_tokens!r}")
    mode, data_file = mode_tokens[0], mode_tokens[1]

    lat_first = cursor.next("lattice").split()
    if not lat_first:
        raise InputValidationError("lattice", "expected a bravais lattice type")
    bravais = lat_first[0]
    pending = lat_first[1:]

    def _pull(field: str) -> str:
        while not pending:
            pending.extend(cursor.next(field).split())
        return pending.pop(0)

    primitive_vectors: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]] | None = None
    if is_aux_or_prv(bravais):
        vec_vals = [_parse_float(_pull("primitive_vectors"), "primitive_vectors") for _ in range(9)]
        primitive_vectors = (
            (vec_vals[0], vec_vals[1], vec_vals[2]),
            (vec_vals[3], vec_vals[4], vec_vals[5]),
            (vec_vals[6], vec_vals[7], vec_vals[8]),
        )
        a = _parse_float(_pull("a"), "a")
        c_over_a, b_over_a, alpha, beta, gamma = 1.0, 1.0, 90.0, 90.0, 90.0
    else:
        a = _parse_float(_pull("a"), "a")
        c_over_a = _parse_opt(_pull("c_over_a"), 1.0, "c_over_a")
        b_over_a = _parse_opt(_pull("b_over_a"), 1.0, "b_over_a")
        alpha = _parse_opt(_pull("alpha"), 90.0, "alpha")
        beta = _parse_opt(_pull("beta"), 90.0, "beta")
        gamma = _parse_opt(_pull("gamma"), 90.0, "gamma")

    # A leftover trailing "," here is harmless padding AkaiKKR itself ignores.
    energy_tokens = cursor.next("edelt").split()
    if len(energy_tokens) < 6:
        raise InputValidationError("edelt", f"expected 'edelt ewidth reltyp sdftyp magtyp record', got {energy_tokens!r}")
    edelt = _parse_float(energy_tokens[0], "edelt")
    ewidth = _parse_float(energy_tokens[1], "ewidth")
    reltyp, sdftyp, magtyp, record = energy_tokens[2], energy_tokens[3], energy_tokens[4], energy_tokens[5]

    out_tokens = cursor.next("outtyp").split()
    if len(out_tokens) < 4:
        raise InputValidationError("outtyp", f"expected 'outtyp bzqlty maxitr pmix', got {out_tokens!r}")
    outtyp = out_tokens[0]
    bzqlty = _parse_bzqlty(out_tokens[1])
    maxitr = _parse_int(out_tokens[2], "maxitr")
    pmix, mixtyp = _split_pmix(out_tokens[3], "pmix")

    ntyp = _parse_int(cursor.next("ntyp").split()[0], "ntyp")

    atom_types: list[AtomType] = []
    for i in range(ntyp):
        header_tokens = cursor.next(f"atom_types[{i}]").split()
        if len(header_tokens) < 5:
            raise InputValidationError(f"atom_types[{i}]", f"expected 'type ncmp rmt field mxl', got {header_tokens!r}")
        name = header_tokens[0]
        ncmp = _parse_int(header_tokens[1], f"atom_types[{name}].ncmp")
        rmt = _parse_float(header_tokens[2], f"atom_types[{name}].rmt")
        at_field = _parse_float(header_tokens[3], f"atom_types[{name}].field")
        lmxtyp = _parse_int(header_tokens[4], f"atom_types[{name}].lmxtyp")

        components: list[AtomicComponent] = []
        inline = header_tokens[5:]
        if inline:
            if len(inline) != 2:
                raise InputValidationError(f"atom_types[{name}].components[0]", f"expected 'anclr conc', got {inline!r}")
            components.append(
                AtomicComponent(
                    anclr=_parse_float(inline[0], f"atom_types[{name}].components[0].anclr"),
                    conc=_parse_float(inline[1], f"atom_types[{name}].components[0].conc") / 100.0,
                )
            )
        while len(components) < ncmp:
            j = len(components)
            comp_tokens = cursor.next(f"atom_types[{name}].components[{j}]").split()
            if len(comp_tokens) != 2:
                raise InputValidationError(
                    f"atom_types[{name}].components[{j}]", f"expected 'anclr conc', got {comp_tokens!r}"
                )
            components.append(
                AtomicComponent(
                    anclr=_parse_float(comp_tokens[0], f"atom_types[{name}].components[{j}].anclr"),
                    conc=_parse_float(comp_tokens[1], f"atom_types[{name}].components[{j}].conc") / 100.0,
                )
            )

        atom_types.append(AtomType(name=name, rmt=rmt, field=at_field, lmxtyp=lmxtyp, components=components))

    natm = _parse_int(cursor.next("natm").split()[0], "natm")

    positions: list[AtomPosition] = []
    for i in range(natm):
        pos_tokens = cursor.next(f"positions[{i}]").split()
        if len(pos_tokens) < 4:
            raise InputValidationError(f"positions[{i}]", f"expected 'x y z atmtyp', got {pos_tokens!r}")
        positions.append(
            AtomPosition(
                x=_parse_coord(pos_tokens[0], f"positions[{i}].x"),
                y=_parse_coord(pos_tokens[1], f"positions[{i}].y"),
                z=_parse_coord(pos_tokens[2], f"positions[{i}].z"),
                atom_type=pos_tokens[3],
            )
        )

    kpath: KPath | None = None
    if mode == "spc":
        trailing = cursor.next_optional()
        if trailing is not None and trailing.split()[0] != "end":
            nkpts = _parse_int(trailing.split()[0], "kpath.nkpts")
            points: list[KPoint] = []
            while True:
                point_line = cursor.next_optional()
                if point_line is None:
                    break
                point_tokens = point_line.split()
                if len(point_tokens) != 3:
                    raise InputValidationError(f"kpath.points[{len(points)}]", f"expected 'x y z', got {point_tokens!r}")
                points.append(KPoint(x=point_tokens[0], y=point_tokens[1], z=point_tokens[2]))
            kpath = KPath(nkpts=nkpts, points=points)

    return cls(
        mode=mode,
        data_file=data_file,
        bravais=bravais,
        a=a,
        atom_types=atom_types,
        positions=positions,
        c_over_a=c_over_a,
        b_over_a=b_over_a,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        edelt=edelt,
        ewidth=ewidth,
        reltyp=reltyp,
        sdftyp=sdftyp,
        magtyp=magtyp,
        record=record,
        outtyp=outtyp,
        bzqlty=bzqlty,
        maxitr=maxitr,
        pmix=pmix,
        mixtyp=mixtyp,
        title=title,
        kpath=kpath,
        primitive_vectors=primitive_vectors,
    )
