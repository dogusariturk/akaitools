"""Parser for AkaiKKR DOS output files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from akaitools.errors import ParseError
from akaitools.models import AtomicComponent, AtomType, DOSComponent, DOSCurve, DOSResult
from akaitools.parsers.common import (
    ATOMIC_SYMBOLS,
    find_all_lines,
    parse_common_sections,
    read_lines,
    scan_numeric_block,
)

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class ComponentMetadata:
    """Public metadata for one DOS component."""

    type_name: str
    symbol: str
    label: str


class DOSParser:
    """Parse AkaiKKR DOS and DSP output files."""

    def parse(self, path: Path | str) -> DOSResult:
        """Parse an AkaiKKR DOS or DSP output file.

        Args:
            path: Path to the DOS or DSP output file.

        Returns:
            The parsed DOS result.
        """
        lines = read_lines(path)
        common = parse_common_sections(lines)

        return DOSResult(
            date=common.header.date,
            time=common.header.time,
            meshr=common.header.meshr,
            mse=common.header.mse,
            ng=common.header.ng,
            mxl=common.header.mxl,
            input_params=common.input_params,
            energy_mesh=common.energy_mesh,
            lattice=common.lattice,
            atom_types=common.atom_types,
            positions=common.positions,
            core_configs=common.core_configs,
            atomic_properties=common.atomic_properties,
            system_info=common.system_info,
            dos_components=parse_dos_components(
                lines,
                common.input_params.ncmpx,
                common.atom_types,
            ),
            total_up=parse_curve_block(lines, r"^ total DOS", 0, spin="up"),
            total_down=parse_curve_block(lines, r"^ total DOS", 1, spin="down"),
            integrated_up=parse_curve_block(lines, r"^ integrated DOS", 0, spin="up"),
            integrated_down=parse_curve_block(lines, r"^ integrated DOS", 1, spin="down"),
        )


def parse_dos_components(
    lines: list[str],
    ncmpx: int,
    atom_types: list[AtomType],
) -> list[DOSComponent]:
    """Parse all component DOS blocks for both spin channels.

    Args:
        lines: Full file content split into lines.
        ncmpx: Number of CPA components in the input.
        atom_types: Parsed atom-type metadata.

    Returns:
        The DOS components in output order.
    """
    header_indices = find_all_lines(lines, r"DOS of component\s+\d+")
    if not header_indices:
        raise ParseError("Missing required section: DOS of component")

    total_dos_markers = find_all_lines(lines, r"^ total DOS")
    if total_dos_markers:
        split_at = total_dos_markers[0]
        up_headers = [index for index in header_indices if index < split_at]
        down_headers = [index for index in header_indices if index > split_at]
    else:
        up_headers = header_indices[:ncmpx]
        down_headers = header_indices[ncmpx:]

    component_metadata = build_component_metadata(atom_types)
    return collect_components(lines, up_headers, "up", component_metadata) + collect_components(
        lines,
        down_headers,
        "down",
        component_metadata,
    )


def collect_components(
    lines: list[str],
    header_indices: list[int],
    spin: str,
    component_metadata: list[ComponentMetadata],
) -> list[DOSComponent]:
    """Build DOS component objects for one spin channel.

    Args:
        lines: Full file content split into lines.
        header_indices: Line indices of component headers for the spin channel.
        spin: Spin label to assign to parsed components.
        component_metadata: Public component metadata by component index.

    Returns:
        The parsed DOS components for the requested spin channel.
    """
    components: list[DOSComponent] = []
    for start in header_indices:
        match = re.search(r"DOS of component\s+(\d+)", lines[start])
        if match is None:
            continue

        component_index = int(match.group(1))
        rows = scan_numeric_block(lines, start)
        if not rows or len(rows[0]) < 4:
            continue

        array = np.array(rows, dtype=np.float64)
        energy = array[:, 0]
        if array.shape[1] == 5:
            s, p, d, total = array[:, 1], array[:, 2], array[:, 3], array[:, 4]
            f = None
        elif array.shape[1] == 6:
            s, p, d, f, total = (
                array[:, 1],
                array[:, 2],
                array[:, 3],
                array[:, 4],
                array[:, 5],
            )
        else:
            raise ParseError(
                f"DOS component {component_index}: unexpected column count {array.shape[1]}; "
                f"expected 5 (s,p,d,total) or 6 (s,p,d,f,total)"
            )

        metadata = (
            component_metadata[component_index - 1]
            if component_index - 1 < len(component_metadata)
            else ComponentMetadata(
                type_name=f"comp{component_index}",
                symbol=f"Z{component_index}",
                label=f"comp{component_index}",
            )
        )
        components.append(
            DOSComponent(
                component_index=component_index,
                type_name=metadata.type_name,
                symbol=metadata.symbol,
                label=metadata.label,
                spin=spin,
                energy=energy,
                s=s,
                p=p,
                d=d,
                f=f,
                total=total,
            )
        )
    return components


def _component_to_metadata(
    atom_type: AtomType,
    component: AtomicComponent | None,
    *,
    multi_component: bool,
) -> ComponentMetadata:
    """Build one ComponentMetadata record from an atom type and optional CPA component.

    Args:
        atom_type: The atom-type record for this site.
        component: The CPA component, or ``None`` for pure (non-CPA) sites.
        multi_component: Whether the site has more than one CPA component.

    Returns:
        The constructed metadata record.
    """
    if component is None:
        return ComponentMetadata(type_name=atom_type.name, symbol=atom_type.name, label=atom_type.name)
    symbol = ATOMIC_SYMBOLS.get(int(component.anclr), f"Z{int(component.anclr)}")
    label = f"{atom_type.name}:{symbol}" if multi_component else atom_type.name
    return ComponentMetadata(type_name=atom_type.name, symbol=symbol, label=label)


def build_component_metadata(atom_types: list[AtomType]) -> list[ComponentMetadata]:
    """Build metadata matching the public DOS component numbering.

    Args:
        atom_types: Parsed atom-type metadata.

    Returns:
        One metadata record per public DOS component.
    """
    metadata: list[ComponentMetadata] = []
    for atom_type in atom_types:
        if not atom_type.components:
            metadata.append(_component_to_metadata(atom_type, None, multi_component=False))
        elif len(atom_type.components) == 1:
            metadata.append(_component_to_metadata(atom_type, atom_type.components[0], multi_component=False))
        else:
            for component in atom_type.components:
                metadata.append(_component_to_metadata(atom_type, component, multi_component=True))
    return metadata


def parse_curve_block(
    lines: list[str],
    marker_pattern: str,
    occurrence: int,
    *,
    spin: str,
) -> DOSCurve | None:
    """Parse a 2-column DOS-like curve block by marker order.

    Args:
        lines: Full file content split into lines.
        marker_pattern: Regex for the block header line.
        occurrence: Zero-based marker occurrence to parse.
        spin: Spin label to attach to the parsed curve.

    Returns:
        The parsed curve, or ``None`` if the block is missing.
    """
    starts = find_all_lines(lines, marker_pattern)
    if occurrence >= len(starts):
        return None

    rows = scan_numeric_block(lines, starts[occurrence])
    if not rows:
        return None
    if any(len(row) != 2 for row in rows):
        raise ParseError(f"Malformed 2-column curve block after marker {marker_pattern!r}")

    array = np.array(rows, dtype=np.float64)
    return DOSCurve(spin=spin, energy=array[:, 0], values=array[:, 1])
