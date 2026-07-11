"""The InputFile dataclass: fields, validation, and construction from a parsed result."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

from akaitools.errors import InputValidationError
from akaitools.input.formatting import format_input_file
from akaitools.input.lattice import is_aux_or_prv
from akaitools.input.parsing import parse_input_file

if TYPE_CHECKING:
    from akaitools.models import AtomPosition, AtomType, CalculationResult, KPath


@dataclass
class InputFile:
    """An AkaiKKR input file.

    Can be constructed directly from individual parameters or reconstructed
    from any parsed ``CalculationResult`` via ``from_result()``.  Call
    ``to_string()`` to render the free-column text that AkaiKKR expects, or
    ``write()`` to save it to disk.

    Attributes:
        mode: Calculation mode — ``"go"``, ``"dos"``, or ``"spc"``.
        data_file: Data file prefix written to the second line of the input
            (e.g. ``"data/fe"``).
        bravais: Bravais lattice type (e.g. ``"bcc"``, ``"fcc"``,
            ``"hexagonal"``).
        a: Lattice constant in bohr.
        atom_types: Ordered list of site-type definitions.  Component
            concentrations must be fractions (0–1) and must sum to 1.0 per
            type.
        positions: Ordered list of fractional atomic positions.
        c_over_a: c/a ratio.  Rendered as ``","`` (AkaiKKR default) when
            equal to ``1.0``.
        b_over_a: b/a ratio.  Same convention as ``c_over_a``.
        alpha: α lattice angle in degrees.  Rendered as ``","`` when ``90.0``.
        beta: β lattice angle in degrees.  Same convention.
        gamma: γ lattice angle in degrees.  Same convention.
        edelt: Energy mesh spacing in Ry.
        ewidth: Energy window half-width in Ry.
        reltyp: Relativistic approximation (``"nrl"``, ``"sra"``, ``"fra"``).
        sdftyp: Exchange-correlation functional (e.g. ``"mjwasa"``,
            ``"mjw"``, ``"ggapw"``).
        magtyp: Magnetic treatment (e.g. ``"mag"``, ``"nmag"``, ``"kick"``,
            or a variant like ``"kick3"``) — AkaiKKR treats this as a free
            string, not a fixed enum.
        record: Record type — ``"2nd"`` or ``"1st"``.
        outtyp: Output type — ``"update"`` or ``"quit"``.
        bzqlty: Brillouin zone mesh quality — an integer mesh count, or one
            of AkaiKKR's quality letter codes (``"t"``, ``"l"``, ``"m"``,
            ``"h"``, ``"u"``).
        maxitr: Maximum number of SCF iterations.
        pmix: Mixing parameter.
        mixtyp: Mixing-type suffix attached directly to ``pmix`` with no
            separator (e.g. ``"br"`` for Broyden, rendered as ``"0.02br"``).
            Empty string means no mixing type is specified.
        title: Optional comment placed on the first line.  Auto-derived from
            ``bravais`` and the first atom-type name when empty.
        kpath: k-point path for Bloch spectral function calculations.  Must
            be ``None`` unless ``mode`` is ``"spc"``.
        primitive_vectors: Three explicit primitive lattice vectors
            ``(v1, v2, v3)``, each a ``(x, y, z)`` tuple in units of ``a``.
            Required when ``bravais`` is ``"aux"`` or ``"prv"`` (AkaiKKR
            reads these instead of ``c_over_a``/``b_over_a``/angles in that
            case); must be ``None`` otherwise.
    """

    mode: str
    data_file: str
    bravais: str
    a: float
    atom_types: list[AtomType]
    positions: list[AtomPosition]

    c_over_a: float = 1.0
    b_over_a: float = 1.0
    alpha: float = 90.0
    beta: float = 90.0
    gamma: float = 90.0
    edelt: float = 0.001
    ewidth: float = 1.0
    reltyp: str = "nrl"
    sdftyp: str = "mjwasa"
    magtyp: str = "mag"
    record: str = "2nd"
    outtyp: str = "update"
    bzqlty: int | str = 8
    maxitr: int = 100
    pmix: float = 0.035
    mixtyp: str = ""
    title: str = ""
    kpath: KPath | None = None
    primitive_vectors: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]] | None = None

    def __post_init__(self) -> None:
        """Validate field consistency after construction.

        Raises:
            InputValidationError: If any field violates a structural constraint.
        """
        valid_modes = frozenset({"go", "dos", "spc"})
        if self.mode not in valid_modes:
            raise InputValidationError(
                "mode",
                f"must be one of {sorted(valid_modes)!r}, got {self.mode!r}",
            )
        if not self.atom_types:
            raise InputValidationError("atom_types", "must not be empty")
        if not self.positions:
            raise InputValidationError("positions", "must not be empty")

        for at in self.atom_types:
            if not at.components:
                raise InputValidationError(
                    f"atom_types[{at.name}].components",
                    "must not be empty",
                )
            total = sum(c.conc for c in at.components)
            if not (0.99 <= total <= 1.01):
                raise InputValidationError(
                    f"atom_types[{at.name}].components",
                    f"concentrations sum to {total:.4f}, expected 1.0",
                )

        defined = {at.name for at in self.atom_types}
        for i, pos in enumerate(self.positions):
            if pos.atom_type not in defined:
                raise InputValidationError(
                    f"positions[{i}].atom_type",
                    f"references undefined type {pos.atom_type!r} (defined: {sorted(defined)})",
                )

        if self.kpath is not None and self.mode != "spc":
            raise InputValidationError(
                "kpath",
                f"only valid when mode='spc', got mode={self.mode!r}",
            )

        if is_aux_or_prv(self.bravais):
            if self.primitive_vectors is None:
                raise InputValidationError(
                    "primitive_vectors",
                    f"required when bravais={self.bravais!r}",
                )
        elif self.primitive_vectors is not None:
            raise InputValidationError(
                "primitive_vectors",
                f"only valid when bravais is 'aux' or 'prv', got bravais={self.bravais!r}",
            )

    @classmethod
    def from_result(
        cls,
        result: CalculationResult,
        *,
        mode: str | None = None,
        kpath: KPath | None = None,
        reset_rmt: bool = False,
    ) -> InputFile:
        """Reconstruct an ``InputFile`` from a parsed AkaiKKR result.

        All scalar parameters are taken from ``result.input_params``.
        Atom types and positions are copied from the result, with an option
        to reset the muffin-tin radii to zero so AkaiKKR recomputes them.

        Args:
            result: Any parsed calculation result (GO, DOS, or SPC).
            mode: Override the calculation mode.  Defaults to the mode recorded in ``result.input_params.go``.
            kpath: k-point path for SPC calculations.  Only valid when ``mode`` is ``"spc"``.
            reset_rmt: When ``True``, sets every muffin-tin radius to ``0.0``
                so AkaiKKR recomputes it automatically on the next run.  Defaults to ``False``, which preserves
                the radii exactly as they appear in the parsed result.

        Returns:
            A new ``InputFile`` ready to render or further modify.

        Raises:
            InputValidationError: If the resolved mode is not a valid AkaiKKR
                mode, or if ``result.input_params.brvtyp`` is ``"aux"``/``"prv"``
                — reconstructing explicit primitive vectors from a parsed
                result is not currently supported.
        """
        p = result.input_params
        resolved_mode = mode if mode is not None else p.go
        valid_modes = frozenset({"go", "dos", "spc"})
        if resolved_mode not in valid_modes:
            raise InputValidationError(
                "mode",
                f"must be one of {sorted(valid_modes)!r}, got {resolved_mode!r}",
            )

        atom_types = [replace(at, rmt=0.0) for at in result.atom_types] if reset_rmt else list(result.atom_types)

        return cls(
            mode=resolved_mode,
            data_file=p.file,
            bravais=p.brvtyp,
            a=p.a,
            c_over_a=p.c_over_a if p.c_over_a != 0.0 else 1.0,
            b_over_a=p.b_over_a if p.b_over_a != 0.0 else 1.0,
            alpha=p.alpha if p.alpha != 0.0 else 90.0,
            beta=p.beta if p.beta != 0.0 else 90.0,
            gamma=p.gamma if p.gamma != 0.0 else 90.0,
            edelt=p.edelt,
            ewidth=p.ewidth,
            reltyp=p.reltyp,
            sdftyp=p.sdftyp,
            magtyp=p.magtyp,
            record=p.record,
            outtyp=p.outtyp,
            bzqlty=p.bzqlty,
            maxitr=int(p.maxitr) if p.maxitr.isdigit() else 100,
            pmix=p.pmix,
            mixtyp=p.mixtyp,
            atom_types=atom_types,
            positions=list(result.positions),
            kpath=kpath,
        )

    @classmethod
    def from_string(cls, text: str) -> InputFile:
        """Parse an AkaiKKR free-column input file into an ``InputFile``.

        This is the inverse of ``to_string()``: it reads an optional title
        comment, mode/data_file line, lattice line, energy/relativistic line,
        outtyp/bzqlty/maxitr/pmix line, atom-type block, and position block,
        following the same free-format conventions ``to_string()`` writes
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
        ``to_string()`` never writes k-point labels, so parsed ``KPoint``
        instances always have ``label=None`` — this is an unrecoverable
        round-trip limitation.

        Args:
            text: The full input-file text.

        Returns:
            The parsed ``InputFile``.

        Raises:
            InputValidationError: If the text is malformed — wrong token
                counts, non-numeric values where numbers are expected, or a
                structural constraint from ``__post_init__`` is violated.
        """
        return parse_input_file(cls, text)

    @classmethod
    def from_file(cls, path: Path | str) -> InputFile:
        """Read an AkaiKKR input file from disk and parse it.

        Args:
            path: Path to the input file.

        Returns:
            The parsed ``InputFile``.

        Raises:
            InputValidationError: If the file content is malformed.
        """
        return cls.from_string(Path(path).read_text(encoding="utf-8"))

    def to_string(self) -> str:
        """Render the input file as a string in AkaiKKR free-column format.

        Returns:
            The complete input file text, terminated by a newline.
        """
        return format_input_file(self)

    def write(self, path: Path | str) -> None:
        """Write the rendered input file to disk.

        Args:
            path: Destination file path.  Parent directories must exist.
        """
        Path(path).write_text(self.to_string(), encoding="utf-8")
