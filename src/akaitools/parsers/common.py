"""Shared parsing utilities for AkaiKKR output files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from akaitools.errors import ParseError
from akaitools.models import (
    AtomicComponent,
    AtomicProperties,
    AtomPosition,
    AtomType,
    CoreConfig,
    EnergyPoint,
    InputParams,
    LatticeInfo,
    SystemInfo,
)
from akaitools.parsers.atomic_properties import parse_atomic_properties

ATOMIC_SYMBOLS: dict[int, str] = {
    1: "H",
    2: "He",
    3: "Li",
    4: "Be",
    5: "B",
    6: "C",
    7: "N",
    8: "O",
    9: "F",
    10: "Ne",
    11: "Na",
    12: "Mg",
    13: "Al",
    14: "Si",
    15: "P",
    16: "S",
    17: "Cl",
    18: "Ar",
    19: "K",
    20: "Ca",
    21: "Sc",
    22: "Ti",
    23: "V",
    24: "Cr",
    25: "Mn",
    26: "Fe",
    27: "Co",
    28: "Ni",
    29: "Cu",
    30: "Zn",
    31: "Ga",
    32: "Ge",
    33: "As",
    34: "Se",
    35: "Br",
    36: "Kr",
    37: "Rb",
    38: "Sr",
    39: "Y",
    40: "Zr",
    41: "Nb",
    42: "Mo",
    43: "Tc",
    44: "Ru",
    45: "Rh",
    46: "Pd",
    47: "Ag",
    48: "Cd",
    49: "In",
    50: "Sn",
    51: "Sb",
    52: "Te",
    53: "I",
    54: "Xe",
    55: "Cs",
    56: "Ba",
    57: "La",
    58: "Ce",
    59: "Pr",
    60: "Nd",
    61: "Pm",
    62: "Sm",
    63: "Eu",
    64: "Gd",
    65: "Tb",
    66: "Dy",
    67: "Ho",
    68: "Er",
    69: "Tm",
    70: "Yb",
    71: "Lu",
    72: "Hf",
    73: "Ta",
    74: "W",
    75: "Re",
    76: "Os",
    77: "Ir",
    78: "Pt",
    79: "Au",
    80: "Hg",
    81: "Tl",
    82: "Pb",
    83: "Bi",
    84: "Po",
    85: "At",
    86: "Rn",
    87: "Fr",
    88: "Ra",
    89: "Ac",
    90: "Th",
    91: "Pa",
    92: "U",
    93: "Np",
    94: "Pu",
    95: "Am",
    96: "Cm",
    97: "Bk",
    98: "Cf",
    99: "Es",
    100: "Fm",
    101: "Md",
    102: "No",
    103: "Lr",
    104: "Rf",
    105: "Db",
    106: "Sg",
    107: "Bh",
    108: "Hs",
    109: "Mt",
    110: "Ds",
    111: "Rg",
    112: "Cn",
    113: "Nh",
    114: "Fl",
    115: "Mc",
    116: "Lv",
    117: "Ts",
    118: "Og",
}

STATE_LABELS: tuple[str, ...] = (
    "1s",
    "2s",
    "2p",
    "3s",
    "3p",
    "3d",
    "4s",
    "4p",
    "4d",
    "5s",
    "5p",
    "4f",
    "5d",
    "6s",
    "6p",
    "5f",
    "6d",
    "7s",
)

_NUMERIC_LINE_RX = re.compile(r"^\s*[-+.\d]")


@dataclass(frozen=True)
class HeaderInfo:
    """Mesh/header metadata parsed from the file preamble."""

    date: str
    time: str
    meshr: int
    mse: int
    ng: int
    mxl: int


@dataclass(frozen=True)
class CommonSections:
    """Common structured sections shared by GO and DOS outputs."""

    header: HeaderInfo
    input_params: InputParams
    energy_mesh: list[EnergyPoint]
    lattice: LatticeInfo
    atom_types: list[AtomType]
    positions: list[AtomPosition]
    core_configs: list[CoreConfig]
    atomic_properties: list[AtomicProperties]
    system_info: SystemInfo


def read_lines(path: Path | str) -> list[str]:
    """Read a text file and return its lines without terminators.

    Args:
        path: Path to the text file.

    Returns:
        The file content split into lines.
    """
    return Path(path).read_text(encoding="utf-8", errors="replace").splitlines()


def find_line(lines: list[str], pattern: str, start: int = 0) -> int:
    """Return the index of the first matching line.

    Args:
        lines: Full file content split into lines.
        pattern: Regular expression to search for.
        start: Line index at which to begin searching.

    Returns:
        The matching line index, or ``-1`` if no match is found.
    """
    regex = re.compile(pattern)
    for index in range(start, len(lines)):
        if regex.search(lines[index]):
            return index
    return -1


def find_all_lines(lines: list[str], pattern: str) -> list[int]:
    """Return the indices of every matching line.

    Args:
        lines: Full file content split into lines.
        pattern: Regular expression to search for.

    Returns:
        The matching line indices in ascending order.
    """
    regex = re.compile(pattern)
    return [index for index, line in enumerate(lines) if regex.search(line)]


def require_line(lines: list[str], pattern: str, *, section: str, start: int = 0) -> int:
    """Find a required section header.

    Args:
        lines: Full file content split into lines.
        pattern: Regular expression to search for.
        section: Human-readable section name for error messages.
        start: Line index at which to begin searching.

    Returns:
        The matching line index.

    Raises:
        ParseError: If the required section is missing.
    """
    index = find_line(lines, pattern, start=start)
    if index == -1:
        raise ParseError(f"Missing required section: {section}")
    return index


def scan_numeric_block(lines: list[str], start: int) -> list[list[float]]:
    """Collect a blank-line-delimited numeric block below a header line.

    Args:
        lines: Full file content split into lines.
        start: Header line index directly above the numeric block.

    Returns:
        The numeric rows converted to floats.
    """
    rows: list[list[float]] = []
    index = start + 1
    while index < len(lines):
        line = lines[index]
        if _NUMERIC_LINE_RX.match(line):
            rows.append([float(value) for value in line.split()])
            index += 1
            continue
        if rows:
            break
        index += 1
    return rows


def parse_common_sections(lines: list[str]) -> CommonSections:
    """Parse the sections shared by GO and DOS outputs.

    Args:
        lines: Full file content split into lines.

    Returns:
        The shared structured sections.
    """
    iteration_start = find_line(lines, r"\*\*\*\*\* self-consistent iteration starts")
    core_section = lines[:iteration_start] if iteration_start != -1 else lines

    return CommonSections(
        header=parse_header(lines),
        input_params=parse_input_params(lines),
        energy_mesh=parse_energy_mesh(lines),
        lattice=parse_lattice(lines),
        atom_types=parse_atom_types(lines),
        positions=parse_positions(lines),
        core_configs=parse_core_configs(core_section),
        atomic_properties=parse_atomic_properties(lines),
        system_info=parse_system_info(lines),
    )


def parse_header(lines: list[str]) -> HeaderInfo:
    """Parse date, time, and mesh parameters from the file header.

    Args:
        lines: Full file content split into lines.

    Returns:
        The parsed header metadata.

    Raises:
        ParseError: If the file is too short or the mesh header is malformed.
    """
    if len(lines) < 4:
        raise ParseError("File is too short to contain an AkaiKKR header")

    values = lines[3].split()
    if len(values) < 4:
        raise ParseError("Header mesh line is malformed")

    return HeaderInfo(
        date=lines[0].strip(),
        time=lines[1].strip(),
        meshr=int(values[0]),
        mse=int(values[1]),
        ng=int(values[2]),
        mxl=int(values[3]),
    )


def parse_input_params(lines: list[str]) -> InputParams:
    """Parse the ``data read in`` block.

    Args:
        lines: Full file content split into lines.

    Returns:
        The parsed input parameters.
    """
    start = require_line(lines, r"data read in", section="data read in")
    block = "\n".join(lines[start : start + 10])

    def value(key: str) -> str:
        match = re.search(rf"{re.escape(key)}=\s*(\S+)", block)
        return match.group(1) if match else ""

    edelt_match = re.search(r"edelt=\s*([\d.E+\-]+)", block)
    ewidth_match = re.search(r"ewidth=\s*([\d.]+)", block)
    bzqlty_match = re.search(r"bzqlty=\s*(\d+)", block)
    maxitr_match = re.search(r"maxitr=\s*(\S+)", block)
    pmix_match = re.search(r"pmix=\s*([\d.E+\-]+)", block)
    ntyp_match = re.search(r"ntyp=\s*(\d+)", block)
    natm_match = re.search(r"natm=\s*(\d+)", block)
    ncmpx_match = re.search(r"ncmpx=\s*(\d+)", block)

    return InputParams(
        go=value("go"),
        file=value("file"),
        brvtyp=value("brvtyp"),
        a=float(value("a")),
        c_over_a=float(value("c/a") or "1.0"),
        b_over_a=float(value("b/a") or "1.0"),
        alpha=float(value("alpha")),
        beta=float(value("beta")),
        gamma=float(value("gamma")),
        edelt=float(edelt_match.group(1)) if edelt_match else 0.0,
        ewidth=float(ewidth_match.group(1)) if ewidth_match else 0.0,
        reltyp=value("reltyp"),
        sdftyp=value("sdftyp"),
        magtyp=value("magtyp"),
        record=value("record"),
        outtyp=value("outtyp"),
        bzqlty=int(bzqlty_match.group(1)) if bzqlty_match else 0,
        maxitr=maxitr_match.group(1) if maxitr_match else "",
        pmix=float(pmix_match.group(1)) if pmix_match else 0.0,
        mixtyp=value("mixtyp"),
        ntyp=int(ntyp_match.group(1)) if ntyp_match else 0,
        natm=int(natm_match.group(1)) if natm_match else 0,
        ncmpx=int(ncmpx_match.group(1)) if ncmpx_match else 0,
    )


def parse_energy_mesh(lines: list[str]) -> list[EnergyPoint]:
    """Parse the complex energy mesh.

    Args:
        lines: Full file content split into lines.

    Returns:
        The parsed complex energy points.
    """
    start = find_line(lines, r"complex energy mesh")
    if start == -1:
        return []

    points: list[EnergyPoint] = []
    for line in lines[start + 1 :]:
        matches = re.findall(r"\(\s*([-\d.]+),\s*([-\d.]+)\)", line)
        if not matches and points:
            break
        for real_part, imag_part in matches:
            points.append(EnergyPoint(real=float(real_part), imag=float(imag_part)))
    return points


def parse_lattice(lines: list[str]) -> LatticeInfo:
    """Parse lattice constants and reciprocal/primitive vectors.

    Args:
        lines: Full file content split into lines.

    Returns:
        The parsed lattice description.
    """
    start = require_line(lines, r"lattice constant", section="lattice constant")
    block = "\n".join(lines[start : start + 15])
    primitive_start = require_line(
        lines,
        r"primitive translation vectors",
        section="primitive translation vectors",
        start=start,
    )
    reciprocal_start = require_line(
        lines,
        r"reciprocal lattice vectors",
        section="reciprocal lattice vectors",
        start=primitive_start,
    )

    def vector(label: str, text: str) -> tuple[float, float, float]:
        match = re.search(rf"{label}=\(\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)", text)
        if match is None:
            raise ParseError(f"Malformed vector line for {label}")
        return float(match.group(1)), float(match.group(2)), float(match.group(3))

    primitive_block = "\n".join(lines[primitive_start : primitive_start + 4])
    reciprocal_block = "\n".join(lines[reciprocal_start : reciprocal_start + 4])

    return LatticeInfo(
        bravais=extract(block, r"bravais=(\S+)"),
        a=float(extract(block, r"\ba=\s*([\d.]+)")),
        c_over_a=float(extract(block, r"c/a=\s*([\d.]+)", default="1.0")),
        b_over_a=float(extract(block, r"b/a=\s*([\d.]+)", default="1.0")),
        alpha=float(extract(block, r"alpha=\s*([\d.]+)", default="90.0")),
        beta=float(extract(block, r"beta=\s*([\d.]+)", default="90.0")),
        gamma=float(extract(block, r"gamma=\s*([\d.]+)", default="90.0")),
        volume=float(extract(block, r"unit cell volume=\s*([\d.]+)", default="0.0")),
        volume_filling=float(extract(block, r"volume filling=\s*([\d.]+)", default="0.0")) / 100.0,
        primitive_vectors=(
            vector("a", primitive_block),
            vector("b", primitive_block),
            vector("c", primitive_block),
        ),
        reciprocal_vectors=(
            vector("ga", reciprocal_block),
            vector("gb", reciprocal_block),
            vector("gc", reciprocal_block),
        ),
    )


def parse_atom_types(lines: list[str]) -> list[AtomType]:
    """Parse the ``type of site`` block.

    Args:
        lines: Full file content split into lines.

    Returns:
        The parsed atom-type definitions.
    """
    start = find_line(lines, r"type of site")
    end = find_line(lines, r"atoms in the unit cell", start=start if start != -1 else 0)
    if start == -1 or end == -1:
        return []

    atom_types: list[AtomType] = []
    current_type: AtomType | None = None
    type_regex = re.compile(r"type=(\S+)\s+rmt=\s*([\d.]+)\s+field=\s*([-\d.]+)\s+lmxtyp=\s*(\d+)")
    component_regex = re.compile(r"component=\s*\d+\s+anclr=\s*([\d.]+)\s+conc=\s*([\d.]+)")

    for line in lines[start + 1 : end]:
        type_match = type_regex.search(line)
        if type_match:
            if current_type is not None:
                atom_types.append(current_type)
            current_type = AtomType(
                name=type_match.group(1),
                rmt=float(type_match.group(2)),
                field=float(type_match.group(3)),
                lmxtyp=int(type_match.group(4)),
            )
            continue

        component_match = component_regex.search(line)
        if component_match and current_type is not None:
            current_type.components.append(
                AtomicComponent(
                    anclr=float(component_match.group(1)),
                    conc=float(component_match.group(2)),
                )
            )

    if current_type is not None:
        atom_types.append(current_type)
    return atom_types


def parse_positions(lines: list[str]) -> list[AtomPosition]:
    """Parse the ``atoms in the unit cell`` block.

    Args:
        lines: Full file content split into lines.

    Returns:
        The parsed atom positions.
    """
    start = find_line(lines, r"atoms in the unit cell")
    if start == -1:
        return []

    positions: list[AtomPosition] = []
    regex = re.compile(r"position=\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+type=(\S+)")
    for line in lines[start + 1 :]:
        match = regex.search(line)
        if match:
            positions.append(
                AtomPosition(
                    x=float(match.group(1)),
                    y=float(match.group(2)),
                    z=float(match.group(3)),
                    atom_type=match.group(4),
                )
            )
        elif positions and not line.strip():
            break
    return positions


def parse_core_configs(lines: list[str]) -> list[CoreConfig]:
    """Parse ``core configuration for Z=N`` blocks.

    Args:
        lines: Full file content split into lines.

    Returns:
        The parsed core configurations.
    """
    configs: list[CoreConfig] = []
    for i, line in enumerate(lines):
        z_match = re.search(r"core configuration for Z=\s*(\d+)", line)
        if z_match is None:
            continue

        state_i = None
        for j in range(i + 1, min(i + 20, len(lines))):
            if lines[j].strip().startswith("state"):
                state_i = j
                break

        if state_i is None or state_i + 2 >= len(lines):
            continue

        up_match = re.search(r"up\s+([\d\s]+)", lines[state_i + 1])
        down_match = re.search(r"down\s+([\d\s]+)", lines[state_i + 2])
        if up_match and down_match:
            up = tuple(int(value) for value in up_match.group(1).split())
            down = tuple(int(value) for value in down_match.group(1).split())
            configs.append(
                CoreConfig(
                    z=int(z_match.group(1)),
                    states=STATE_LABELS[: len(up)],
                    up=up,
                    down=down,
                )
            )
    return configs


def parse_system_info(lines: list[str]) -> SystemInfo:
    """Parse the OS and timing block at the end of the file.

    Args:
        lines: Full file content split into lines.

    Returns:
        The parsed system metadata.
    """
    start = find_line(lines, r"^ OS:")
    if start == -1:
        start = find_line(lines, r"OS: ")
    if start == -1:
        return SystemInfo(
            os="",
            host="",
            machine="",
            num_cores=0,
            elapsed_time=0.0,
            num_threads=0,
        )

    block = "\n".join(lines[start : start + 6])
    elapsed_match = re.search(r"elapsed time\s+([\d.]+)\s+sec\s+\(\s*(\d+)\s+threads\)", block)
    return SystemInfo(
        os=extract(block, r"OS:\s+(\S+)", default=""),
        host=extract(block, r"Host:\s+(\S+)", default=""),
        machine=extract(block, r"Machine:\s+(\S+)", default=""),
        num_cores=int(extract(block, r"numcor:\s+(\d+)", default="0")),
        elapsed_time=float(elapsed_match.group(1)) if elapsed_match else 0.0,
        num_threads=int(elapsed_match.group(2)) if elapsed_match else 0,
    )


def extract(text: str, pattern: str, *, default: str | None = None) -> str:
    """Extract the first regex group from a string.

    Args:
        text: Text to search.
        pattern: Regular expression with at least one capture group.
        default: Fallback value when no match is found.

    Returns:
        The first captured value or the provided default.

    Raises:
        ParseError: If no match is found and no default is provided.
    """
    match = re.search(pattern, text)
    if match is not None:
        return match.group(1)
    if default is not None:
        return default
    raise ParseError(f"Could not match required pattern: {pattern}")
