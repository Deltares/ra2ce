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

from dataclasses import dataclass, field

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_result.analysis_result import AnalysisResult
from ra2ce.analysis.analysis_result.analysis_result_wrapper_protocol import (
    AnalysisResultWrapperProtocol,
)


@dataclass(kw_only=True)
class AnalysisResultWrapper(AnalysisResultWrapperProtocol):
    """
    Dataclass to wrap a collection of analysis results.
    """

    results_collection: list[AnalysisResult] = field(default_factory=lambda: [])

    def get_single_result(self) -> GeoDataFrame | None:
        """
        Returns the first declared analysis result if exists, otherwise None.

        Returns:
            GeoDataFrame | None: First declared analysis result.
        """
        if any(self.results_collection):
            return self.results_collection[0].analysis_result
        return None

    def is_valid_result(self) -> bool:
        return any(self.results_collection) and all(
            map(AnalysisResult.is_valid_result, self.results_collection)
        )
