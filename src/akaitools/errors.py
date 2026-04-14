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


class InputValidationError(ValueError):
    """Signal that an ``InputFile`` was constructed with invalid parameters.

    This exception is raised when field values are structurally inconsistent —
    for example, an empty atom-type list, component concentrations that do not
    sum to 1.0, a position referencing an undefined type name, or a k-path
    supplied for a non-SPC mode.

    The ``field`` attribute names the offending field so callers can
    programmatically distinguish which constraint was violated.

    Attributes:
        field: Dot/bracket notation identifying the invalid field
            (e.g. ``"mode"``, ``"atom_types[NiFe].components"``).
    """

    def __init__(self, field: str, message: str) -> None:
        """Initialise the exception with the offending field name and a message.

        Args:
            field: Dot/bracket notation identifying the invalid field
                (e.g. ``"mode"``, ``"atom_types[NiFe].components"``).
            message: Human-readable description of the constraint violation.
        """
        self.field = field
        super().__init__(f"{field}: {message}")
