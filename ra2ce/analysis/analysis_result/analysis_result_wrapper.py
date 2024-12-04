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

from dataclasses import dataclass
from pathlib import Path

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionAdaptation,
    AnalysisSectionDamages,
    AnalysisSectionLosses,
)


@dataclass(kw_only=True)
class AnalysisResultWrapper:
    """
    Dataclass to wrap one (or many) analysis results with their related analysis configuration.
    """

    analyses_results: list[GeoDataFrame]
    analysis_config: AnalysisSectionLosses | AnalysisSectionDamages | AnalysisSectionAdaptation
    output_path: Path

    _custom_name: str = ""

    @property
    def analysis_name(self) -> str:
        """
        Gets the analysis name from the configuration and formats it for exporting.

        Returns:
            str: The formatted analysis name.
        """
        if not self._custom_name:
            return self.analysis_config.name.replace(" ", "_")
        return self._custom_name

    @analysis_name.setter
    def analysis_name(self, new_name: str):
        self._custom_name = new_name

    @property
    def base_export_path(self) -> Path:
        """
        Gets the base export path to use for different formats..

        Returns:
            Path: base path without extension for exporting results.
        """
        return self.output_path.joinpath(
            self.analysis_config.analysis.config_value, self.analysis_name
        )

    def get_single_analysis(self) -> GeoDataFrame | None:
        """
        Returns the first declared analysis result if exists, otherwise None.

        Returns:
            GeoDataFrame | None: First declared analysis result.
        """
        if any(self.analyses_results):
            return self.analyses_results[0]
        return None

    def is_valid_result(self) -> bool:
        """
        Validates whether the `analyses_results` in this wrapper are all valid.

        Returns:
            bool: validation of `analyses_results`.
        """

        def valid_analysis(analysis_gdf: GeoDataFrame) -> bool:
            return isinstance(analysis_gdf, GeoDataFrame) and not analysis_gdf.empty

        return any(self.analyses_results) and all(
            map(valid_analysis, self.analyses_results)
        )
