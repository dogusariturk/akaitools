"""Tests for the GO output file parser."""

from __future__ import annotations

import akaitools


def test_scf_aliases_removed() -> None:
    """Check that the old SCF API aliases are absent."""
    assert not hasattr(akaitools, "parse_scf")
    assert not hasattr(akaitools, "SCFParser")
    assert not hasattr(akaitools, "SCFResult")
    assert not hasattr(akaitools, "SCFIteration")
