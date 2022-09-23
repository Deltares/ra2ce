from typing import Protocol

from ra2ce.validation.validation_report import ValidationReport


class Ra2ceIoValidator(Protocol):
    def validate(self) -> ValidationReport:
        """
        Generates a `ValidationReport` based on its inner-defined criteria.

        Returns:
            ValidationReport: Result of the internal checks.
        """
        pass
