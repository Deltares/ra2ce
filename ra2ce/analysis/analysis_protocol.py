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

from pathlib import Path
from typing import Protocol

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisSectionBase
from ra2ce.network.graph_files.graph_files_protocol import GraphFileProtocol


class AnalysisProtocol(Protocol):
    graph_file: GraphFileProtocol
    analysis: AnalysisSectionBase
    input_path: Path
    output_path: Path
    result: GeoDataFrame

    def execute(self) -> GeoDataFrame:
        """
        Execute the analysis on the given graph/network with the given analysis parameters.
        The resulting (Geo)DataFrame of the analysis is stored in the result attribute.
        TODO: Make the return type a result object #318

        Returns:
            GeoDataFrame: The result of the analysis.
        """
        pass
