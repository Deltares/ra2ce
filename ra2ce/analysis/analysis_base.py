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

from abc import ABC

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_protocol import AnalysisProtocol
from ra2ce.analysis.analysis_result.analysis_result import AnalysisResult
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper


class AnalysisBase(ABC, AnalysisProtocol):
    """
    Abstract class to help extend common functionality among the analysis implementing
    the `AnalysisProtocol`.
    """

    def _get_analysis_result(
        self, gdf_result: GeoDataFrame, custom_name: str
    ) -> AnalysisResult:
        _ar = AnalysisResult(
            analysis_result=gdf_result,
            analysis_config=self.analysis,
            output_path=self.output_path,
        )
        if custom_name:
            _ar.analysis_name = custom_name
        return _ar

    def generate_result_wrapper(
        self, *analysis_result: GeoDataFrame
    ) -> AnalysisResultWrapper:
        """
        Creates a result wrapper based on a given `GeoDataFrame` result for
        the calling analysis (`AnalysisProtocol`).

        Args:
            analysis_result (list[GeoDataFrame]): Resulting dataframes of an analysis.

        Returns:
            AnalysisResultWrapper: Wrapping result with configuration details.
        """

        return AnalysisResultWrapper(
            results_collection=[
                self._get_analysis_result(_ar, "") for _ar in analysis_result
            ]
        )
