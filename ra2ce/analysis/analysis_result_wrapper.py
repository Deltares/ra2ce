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

    analysis_result: GeoDataFrame

    output_path: Path

    # AnalysisProtocol options
    analysis_config: AnalysisSectionLosses | AnalysisSectionDamages | AnalysisSectionAdaptation

    @property
    def base_export_path(self) -> Path:
        """
        Gets the base export path to use for different formats..

        Returns:
            Path: base path without extension for exporting results.
        """
        _analysis_name = self.analysis_config.name.replace(" ", "_")
        return self.output_path.joinpath(_analysis_name)

    def is_valid_result(self) -> bool:
        """
        Validates whether the `analysis_result` in this wrapper is valid.

        Returns:
            bool: validity of `analysis_result`.
        """
        return (
            isinstance(self.analysis_result, GeoDataFrame)
            and not self.analysis_result.empty
        )
