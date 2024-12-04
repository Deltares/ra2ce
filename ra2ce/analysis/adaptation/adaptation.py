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
from copy import deepcopy
from pathlib import Path

from geopandas import GeoDataFrame

from ra2ce.analysis.adaptation.adaptation_option_collection import (
    AdaptationOptionCollection,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionAdaptation,
)
from ra2ce.analysis.analysis_input.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.network.graph_files.network_file import NetworkFile


class Adaptation(AnalysisBase, AnalysisDamagesProtocol):
    analysis: AnalysisSectionAdaptation
    graph_file: NetworkFile
    graph_file_hazard: NetworkFile
    input_path: Path
    output_path: Path
    adaptation_collection: AdaptationOptionCollection

    # TODO: add the proper protocol for the adaptation analysis.
    def __init__(
        self, analysis_input: AnalysisInputWrapper, analysis_config: AnalysisConfigData
    ):
        self.analysis = analysis_input.analysis
        self.graph_file = analysis_input.graph_file
        self.graph_file_hazard = analysis_input.graph_file_hazard
        self.input_path = analysis_input.input_path
        self.output_path = analysis_input.output_path
        self.adaptation_collection = AdaptationOptionCollection.from_config(
            analysis_config
        )

    def execute(self) -> GeoDataFrame:
        """
        Run the adaptation analysis.
        """
        return self.generate_result_wrapper(self.calculate_bc_ratio())

    def run_cost(self) -> GeoDataFrame:
        """
        Calculate the cost for all adaptation options.
        """
        # Open the network without hazard data
        _cost_gdf = deepcopy(self.graph_file.get_graph())
        for (
            _option,
            _cost,
        ) in self.adaptation_collection.calculate_option_cost().items():
            _cost_gdf[f"costs_{_option.id}"] = _cost

        return _cost_gdf

    def run_benefit(self) -> GeoDataFrame:
        """
        Calculate the benefit for all adaptation options
        """
        return None

    def calculate_bc_ratio(self) -> GeoDataFrame:
        """
        Calculate the benefit-cost ratio for all adaptation options
        """
        _cost_gdf = self.run_cost()
        _benefit_gdf = self.run_benefit()
        return None
