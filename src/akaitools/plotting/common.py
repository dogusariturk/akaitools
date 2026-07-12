"""Shared plotting internals for AkaiKKR result visualization."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

__all__ = ["plt", "scientific_mathtext_formatter"]


def scientific_mathtext_formatter() -> ScalarFormatter:
    """Return a scalar formatter with 10^n math text and no additive offset."""
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_useOffset(False)
    return formatter
