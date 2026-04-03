"""Tests for akaitools.errors."""

from __future__ import annotations

import pytest

from akaitools.errors import ParseError


def test_parse_error_is_value_error() -> None:
    """ParseError must be a subclass of ValueError."""
    assert issubclass(ParseError, ValueError)


def test_parse_error_can_be_raised_and_caught() -> None:
    """ParseError raised inside a try block is caught as ValueError."""
    with pytest.raises(ValueError, match="bad file"):
        raise ParseError("bad file")


def test_parse_error_carries_message() -> None:
    """ParseError preserves the error message."""
    exc = ParseError("unexpected column count 3")
    assert "unexpected column count 3" in str(exc)


def test_parse_error_caught_as_itself() -> None:
    """ParseError is catchable by its own type."""
    with pytest.raises(ParseError):
        raise ParseError("missing section")
