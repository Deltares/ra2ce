"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Stichting Deltares

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import logging
from typing import Any


class ValidationReport:
    _errors: list[str]
    _warns: list[str]

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
