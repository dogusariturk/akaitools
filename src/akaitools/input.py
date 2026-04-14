"""AkaiKKR input file generation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

from akaitools.errors import InputValidationError

if TYPE_CHECKING:
    from akaitools.models import AtomPosition, AtomType, CalculationResult, KPath

_VALID_MODES: frozenset[str] = frozenset({"go", "dos", "spc"})
_SEP = "c" + "-" * 60


def _flt(value: float) -> str:
    """Format a float, preserving at least one decimal place."""
    s = f"{value:g}"
    return s if ("." in s or "e" in s) else s + ".0"


def _opt(value: float, default: float) -> str:
    """Return the value as a string or ``","`` when it equals the default."""
    return _flt(value) if value != default else ","


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
        magtyp: Magnetic treatment — ``"mag"`` or ``"nmag"``.
        record: Record type — ``"2nd"`` or ``"1st"``.
        outtyp: Output type — ``"update"`` or ``"quit"``.
        bzqlty: Brillouin zone mesh quality (integer).
        maxitr: Maximum number of SCF iterations.
        pmix: Mixing parameter.
        title: Optional comment placed on the first line.  Auto-derived from
            ``bravais`` and the first atom-type name when empty.
        kpath: k-point path for Bloch spectral function calculations.  Must
            be ``None`` unless ``mode`` is ``"spc"``.
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
    bzqlty: int = 8
    maxitr: int = 100
    pmix: float = 0.035
    title: str = ""
    kpath: KPath | None = None

    def __post_init__(self) -> None:
        """Validate field consistency after construction.

        Raises:
            InputValidationError: If any field violates a structural constraint.
        """
        if self.mode not in _VALID_MODES:
            raise InputValidationError(
                "mode",
                f"must be one of {sorted(_VALID_MODES)!r}, got {self.mode!r}",
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
            InputValidationError: If the resolved mode is not a valid AkaiKKR mode.
        """
        p = result.input_params
        resolved_mode = mode if mode is not None else p.go
        if resolved_mode not in _VALID_MODES:
            raise InputValidationError(
                "mode",
                f"must be one of {sorted(_VALID_MODES)!r}, got {resolved_mode!r}",
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
            atom_types=atom_types,
            positions=list(result.positions),
            kpath=kpath,
        )

    def to_string(self) -> str:
        """Render the input file as a string in AkaiKKR free-column format.

        Returns:
            The complete input file text, terminated by a newline.
        """
        title = self.title or f"{self.bravais.upper()} {self.atom_types[0].name}"

        lat_line = (
            f"    {self.bravais:<10s} {self.a:<8g}"
            f" {_opt(self.c_over_a, 1.0):<6s}"
            f" {_opt(self.b_over_a, 1.0):<6s}"
            f" {_opt(self.alpha, 90.0):<7s}"
            f" {_opt(self.beta, 90.0):<5s}"
            f" {_opt(self.gamma, 90.0):<7s}"
            f" ,"
        )

        lines = [
            f"c--- {title} ---",
            f"    {self.mode}   {self.data_file}",
            _SEP,
            "c   brvtyp     a        c/a   b/a   alpha   beta   gamma",
            lat_line,
            _SEP,
            "c   edelt    ewidth    reltyp   sdftyp   magtyp   record",
            f"    {_flt(self.edelt):<9s} {_flt(self.ewidth):<9s} {self.reltyp:<9s} {self.sdftyp:<9s} {self.magtyp:<9s} {self.record}",
            _SEP,
            "c   outtyp    bzqlty   maxitr   pmix",
            f"    {self.outtyp:<10s} {self.bzqlty:<8d} {self.maxitr:<8d} {self.pmix:g}",
            _SEP,
            "c    ntyp",
            f"     {len(self.atom_types)}",
            _SEP,
            "c   type    ncmp    rmt    field   mxl  anclr   conc",
        ]

        for at in self.atom_types:
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
            _SEP,
            "c   natm",
            f"     {len(self.positions)}",
            _SEP,
            "c   atmicx(in the unit of a)     atmtyp",
        ]

        for pos in self.positions:
            lines.append(f"     {pos.x:<10g} {pos.y:<10g} {pos.z:<10g} {pos.atom_type}")

        lines.append(_SEP)

        if self.mode != "spc":
            lines.append(" end")
        elif self.kpath is not None:
            lines.append(f" {self.kpath.nkpts}")
            for pt in self.kpath.points:
                lines.append(f" {pt.x} {pt.y} {pt.z}")

        return "\n".join(lines) + "\n"

    def write(self, path: Path | str) -> None:
        """Write the rendered input file to disk.

        Args:
            path: Destination file path.  Parent directories must exist.
        """
        Path(path).write_text(self.to_string(), encoding="utf-8")
