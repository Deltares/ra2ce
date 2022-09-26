import logging
from typing import Any


class ValidationReport:
    def __init__(self) -> None:
        self._errors = []
        self._warns = []

    def error(self, error_mssg: str) -> None:
        logging.error(error_mssg)
        self._errors.append(error_mssg)

    def warn(self, warn_mssg: str) -> None:
        logging.warning(warn_mssg)
        self._warns.append(warn_mssg)

    def is_valid(self) -> bool:
        return not any(self._errors)

    def merge(self, with_report: Any) -> None:
        """
        Merges a given report with the current one.

        Args:
            with_report (Any): ValidationReport that will be merged.
        """
        self._errors.extend(with_report._errors)
        self._warns.extend(with_report._warns)
