"""Shared Bravais-lattice-type helpers for AkaiKKR input files."""

from __future__ import annotations


def is_aux_or_prv(bravais: str) -> bool:
    """Return whether a Bravais-type token requests explicit primitive vectors.

    AkaiKKR treats ``brvtyp`` values containing ``"aux"`` or ``"prv"`` specially:
    instead of ``c/a``, ``b/a``, and the three lattice angles, the input supplies
    the three primitive vectors directly.

    Args:
        bravais: The raw ``brvtyp`` token.

    Returns:
        ``True`` if the token requests explicit primitive vectors.
    """
    lowered = bravais.lower()
    return "aux" in lowered or "prv" in lowered
