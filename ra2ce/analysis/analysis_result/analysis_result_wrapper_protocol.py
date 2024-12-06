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

from typing import Protocol, runtime_checkable

from ra2ce.analysis.analysis_result.analysis_result import AnalysisResult


@runtime_checkable
class AnalysisResultWrapperProtocol(Protocol):
    results_collection: list[AnalysisResult]

    def is_valid_result(self) -> bool:
        """
        Validates whether the "analysis results" (`results_collection`) in this wrapper are all valid.

        Returns:
            bool: validation of `results_collection`.
        """
