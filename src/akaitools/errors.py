"""Project-specific exceptions."""

from __future__ import annotations


class ParseError(ValueError):
    """Signal that a file cannot be parsed as a supported AkaiKKR output.

    This exception is raised when a required section is missing or when a
    section is present but malformed.
    """


class InvalidParameterError(ValueError):
    """Signal that a function was called with an unsupported argument value.

    This exception is raised when a caller passes a value that is not in the
    set of accepted choices for a parameter (e.g. an unknown energy unit,
    spin channel, orbital name, or convergence field).
    """
