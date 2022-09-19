from typing import Protocol

from ra2ce.validation.validation_report import ValidationReport


class Ra2ceIoValidator(Protocol):
    def validate(self) -> ValidationReport:
        pass
