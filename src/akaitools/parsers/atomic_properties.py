"""Atomic-property block parsing."""

from __future__ import annotations

import re

from akaitools.models import (
    AtomicProperties,
    ChargeDensityAtNucleus,
    HyperfineField,
    ValenceCharge,
)

_PROPERTY_BLOCK_RX = re.compile(r"\*\*\* type-(\S+)\s+(\w+)\s+\(z=\s*([\d.]+)\)")


def parse_atomic_properties(lines: list[str]) -> list[AtomicProperties]:
    """Parse per-type and per-component property blocks.

    Args:
        lines: Full file content split into lines.

    Returns:
        The parsed atomic-property records.
    """
    block_starts = [index for index, line in enumerate(lines) if _PROPERTY_BLOCK_RX.search(line)]
    if not block_starts:
        return []

    properties: list[AtomicProperties] = []
    for index, start in enumerate(block_starts):
        end = block_starts[index + 1] if index + 1 < len(block_starts) else len(lines)
        block = lines[start:end]
        match = _PROPERTY_BLOCK_RX.search(block[0])
        if match is None:
            continue

        block_text = "\n".join(block)
        total_charge_match = re.search(
            r"total charge=\s*([\d.]+)\s+valence charge \(up/down\)=\s*([\d.]+)\s+([\d.]+)",
            block_text,
        )
        spin_moment_match = re.search(r"spin moment=\s*([-\d.]+)", block_text)
        orbital_moment_match = re.search(r"orbital moment=\s*([-\d.]+)", block_text)
        core_charge_match = re.search(
            r"core charge in the muffin-tin sphere\s*=\s*([\d.]+)",
            block_text,
        )

        properties.append(
            AtomicProperties(
                type_name=match.group(1),
                element=match.group(2),
                z=float(match.group(3)),
                core_charge_muffin_tin=float(core_charge_match.group(1)) if core_charge_match else 0.0,
                valence_up=parse_valence_charge(block_text, "spin up"),
                valence_down=parse_valence_charge(block_text, "spin down"),
                total_charge=float(total_charge_match.group(1)) if total_charge_match else 0.0,
                valence_charge_up=float(total_charge_match.group(2)) if total_charge_match else 0.0,
                valence_charge_down=float(total_charge_match.group(3)) if total_charge_match else 0.0,
                spin_moment=float(spin_moment_match.group(1)) if spin_moment_match else 0.0,
                orbital_moment=float(orbital_moment_match.group(1)) if orbital_moment_match else 0.0,
                core_levels_up=parse_core_levels(block_text, "spin up"),
                core_levels_down=parse_core_levels(block_text, "spin down"),
                hyperfine_field=parse_hyperfine_field(block_text),
                charge_density_at_nucleus=parse_charge_density_at_nucleus(block_text),
            )
        )
    return properties


def parse_valence_charge(block_text: str, spin_label: str) -> ValenceCharge:
    """Extract orbital-resolved valence charge for one spin channel.

    Args:
        block_text: Text for one atomic-property block.
        spin_label: Spin label to match inside the block.

    Returns:
        The parsed valence charge data.
    """
    match = re.search(
        rf"valence charge in the cell \({spin_label}\s*\)"
        r"\s*=\s*([\d.]+)\(s\)\s+([\d.]+)\(p\)\s+([\d.]+)\(d\)"
        r"(?:\s+([\d.]+)\(f\))?",
        block_text,
    )
    if match is None:
        return ValenceCharge(s=0.0, p=0.0, d=0.0)
    return ValenceCharge(
        s=float(match.group(1)),
        p=float(match.group(2)),
        d=float(match.group(3)),
        f=float(match.group(4)) if match.group(4) else None,
    )


def parse_core_levels(block_text: str, spin_label: str) -> dict[str, float]:
    """Extract core-level binding energies for one spin channel.

    Args:
        block_text: Text for one atomic-property block.
        spin_label: Spin label to match inside the block.

    Returns:
        A mapping from orbital label to binding energy.
    """
    match = re.search(
        rf"core level\s+\({spin_label}\s*\)(.*?)(?=core level|hyperfine|$)",
        block_text,
        re.DOTALL,
    )
    if match is None:
        return {}

    return {state: float(value) for value, state in re.findall(r"([-\d.]+)\s+Ry\((\w+)\)", match.group(1))}


def parse_hyperfine_field(block_text: str) -> HyperfineField | None:
    """Parse the hyperfine field entry in one atomic-property block.

    Args:
        block_text: Text for one atomic-property block.

    Returns:
        The parsed hyperfine field data, or ``None`` if the block is absent.
    """
    match = re.search(
        r"hyperfine field of \w+"
        r"\s*([-\d.]+)\s+kG\s+\(core=\s*([-\d.]+)\s+kG\s+valence=\s*([-\d.]+)\s+kG"
        r"\s+orbital=\s*([-\d.]+)\s+kG\s*\)",
        block_text,
    )
    if match is None:
        return None

    start = block_text.find(match.group(0))
    next_section = block_text.find("charge density at the nucleus", start + 1)
    end = next_section if next_section != -1 else len(block_text)
    contribution_block = block_text[start:end]
    core_contributions: dict[str, float] = {}
    for value, state in re.findall(r"([-\d.]+)\s+kG\((\w+)\)", contribution_block):
        core_contributions[state] = float(value)

    return HyperfineField(
        total=float(match.group(1)),
        core=float(match.group(2)),
        valence=float(match.group(3)),
        orbital=float(match.group(4)),
        core_contributions=core_contributions,
    )


def parse_charge_density_at_nucleus(block_text: str) -> ChargeDensityAtNucleus | None:
    """Parse the charge density at the nucleus entry.

    Args:
        block_text: Text for one atomic-property block.

    Returns:
        The parsed charge density data, or ``None`` if the block is absent.
    """
    match = re.search(
        r"charge density at the nucleus\s*\n\s*([\d.]+)\s+\(core=\s*([\d.]+)"
        r"\s+valence=\s*([\d.]+)\s*\)",
        block_text,
    )
    if match is None:
        return None

    start = block_text.find(match.group(0))
    contribution_block = block_text[start:]
    core_contributions: dict[str, float] = {}
    for line in contribution_block.split("\n")[2:5]:
        for value, state in re.findall(r"([\d.]+)\((\w+)\)", line):
            core_contributions[state] = float(value)

    return ChargeDensityAtNucleus(
        total=float(match.group(1)),
        core=float(match.group(2)),
        valence=float(match.group(3)),
        core_contributions=core_contributions,
    )
