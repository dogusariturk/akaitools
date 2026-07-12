"""Tests for a synthetic non-converged AkaiKKR GO output file."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from akaitools import parse_go

if TYPE_CHECKING:
    from pathlib import Path

    from akaitools.models import GOResult


class TestFeNoConvergenceGO:
    """Regression tests for a GO output that hits maxitr without converging."""

    @pytest.fixture(autouse=True)
    def result(self, fe_noconv_go: Path) -> None:
        """Parse the synthetic non-converged Fe GO fixture for each test."""
        self.r: GOResult = parse_go(fe_noconv_go)

    def test_convergence(self) -> None:
        """Check that the calculation is reported as not converged."""
        assert self.r.converged is False
        assert len(self.r.iterations) == 15

    def test_final_iteration_does_not_converge(self) -> None:
        """Check the final iteration still has a large rms error."""
        last = self.r.iterations[-1]
        assert abs(last.rms_error) > 0.1

    def test_lattice_still_parsed(self) -> None:
        """Check that lattice info is unaffected by non-convergence."""
        assert self.r.lattice.bravais == "bcc"
        assert self.r.lattice.a == pytest.approx(5.27, rel=1e-4)

    def test_atomic_properties_still_parsed(self) -> None:
        """Check that post-processing property blocks are still parsed."""
        assert len(self.r.atomic_properties) == 1
        assert self.r.atomic_properties[0].element == "Fe"

    def test_system_info_still_parsed(self) -> None:
        """Check that the trailing system info footer is still parsed."""
        si = self.r.system_info
        assert si.os == "Linux"
        assert si.num_cores == 18
