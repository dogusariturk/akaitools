"""Project-specific exceptions."""

from __future__ import annotations


class ParseError(ValueError):
    """Signal that a file cannot be parsed as a supported AkaiKKR output.

    This exception is raised when a required section is missing or when a
    section is present but malformed.
    """
