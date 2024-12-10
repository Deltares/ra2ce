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

from geopandas import GeoDataFrame

from ra2ce.analysis.adaptation.adaptation_option_collection import (
    AdaptationOptionCollection,
)
from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionAdaptation,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.network.graph_files.network_file import NetworkFile


class Adaptation(AnalysisBase, AnalysisDamagesProtocol):
    """
    Execute the adaptation analysis.
    For each adaptation option a damages and losses analysis is executed.
    """

    analysis: AnalysisSectionAdaptation
    graph_file: NetworkFile
    input_path: Path
    output_path: Path
    adaptation_collection: AdaptationOptionCollection

    # TODO: add the proper protocol for the adaptation analysis.
    def __init__(
        self,
        analysis_input: AnalysisInputWrapper,
        analysis_config: AnalysisConfigWrapper,
    ):
        self.analysis = analysis_input.analysis
        self.graph_file = analysis_input.graph_file
        self.graph_file_hazard = analysis_input.graph_file_hazard
        self.adaptation_collection = AdaptationOptionCollection.from_config(
            analysis_config
        )

    def execute(self) -> AnalysisResultWrapper:
        """
        Run the adaptation analysis.

        Returns:
            AnalysisResultWrapper: The result of the adaptation analysis.
        """
        _cost_gdf = self.run_cost()
        _benefit_gdf = self.run_benefit()

        return self.generate_result_wrapper(
            self.calculate_bc_ratio(_benefit_gdf, _cost_gdf)
        )

    def run_cost(self) -> GeoDataFrame:
        """
        Calculate the link cost for all adaptation options.

        Returns:
            GeoDataFrame: The result of the cost calculation.
        Returns:
            GeoDataFrame: The result of the cost calculation.
        """
        _orig_gdf = self.graph_file.get_graph()

        _cost_gdf = GeoDataFrame()
        for (
            _option,
            _cost,
        ) in self.adaptation_collection.calculate_options_unit_cost().items():
            _cost_gdf[f"{_option.id}_cost"] = _orig_gdf.apply(
                lambda x, cost=_cost: x["length"] * cost, axis=1
            )

        return _cost_gdf

    def run_benefit(self) -> GeoDataFrame:
        """
        Calculate the benefit for all adaptation options.

        Returns:
            GeoDataFrame: The result of the benefit calculation.
        """
        return self.adaptation_collection.calculate_options_benefit()

    def calculate_bc_ratio(
        self, benefit_gdf: GeoDataFrame, cost_gdf: GeoDataFrame
    ) -> GeoDataFrame:
        """
        Calculate the benefit-cost ratio for all adaptation options.

        Args:
            benefit_gdf (GeoDataFrame): Gdf containing the benefit of the adaptation options.
            cost_gdf (GeoDataFrame): Gdf containing the cost of the adaptation options.

        Returns:
            GeoDataFrame: Gdf containing the benefit-cost ratio of the adaptation options.
        """
        for _option in self.adaptation_collection.adaptation_options:
            benefit_gdf[f"{_option.id}_cost"] = cost_gdf[f"{_option.id}_cost"]
            benefit_gdf[f"{_option.id}_bc_ratio"] = benefit_gdf[
                f"{_option.id}_benefit"
            ].replace(float("nan"), 0) / benefit_gdf[f"{_option.id}_cost"].replace(
                0, float("nan")
            )

        return benefit_gdf
